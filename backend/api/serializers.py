from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from api.custom_fields import Base64ImageField
# модель юзера получил в food.models, оттуда везде и импортирую
from food.models import (Favourite, Ingredient, Recipe, RecipeIngredient,
                         ShoppingCart, Tag, User)
from foodgram_user.models import Subscribe


class UserAvatarSeriazlier(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


# class UserUpdatePasswordSerializer(serializers.Serializer):
#     new_password = serializers.CharField()
#     current_password = serializers.CharField()

#     def validate(self, attrs):
#         request = self.context.get('request')
#         user = get_object_or_404(User, email=request.user.email)
#         if not user.check_password(attrs['current_password']):
#             raise serializers.ValidationError('Incorrect password')
#         attrs['USER'] = user
#         return attrs


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('user', None)
        if user is None or not user.is_authenticated:
            return False
        return Subscribe.objects.filter(user=user, subscription=obj).exists()


# class UserCreateSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         fields = ('email', 'username', 'first_name', 'last_name', 'password')

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data.pop('password')
#         data['id'] = instance.id
#         return data

#     def create(self, validated_data):
#         return User.objects.create_user(**validated_data)


class ShoppingCartFavouriteSerializerResponse(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionReadSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField('get_recipes')
    recipes_count = serializers.SerializerMethodField('get_recipes_count')

    class Meta(UserReadSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        return ShoppingCartFavouriteSerializerResponse(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ('user', 'subscription')

    def to_representation(self, instance):
        return SubscriptionReadSerializer(instance.subscription).data

    # 500 django.db.utils.IntegrityError без него
    def validate(self, data):
        user = data['user']
        subscription = data['subscription']
        if user == subscription:
            raise serializers.ValidationError("Cannot subscribe to yourself")
        if Subscribe.objects.filter(
            user=user, subscription=subscription
        ).exists():
            raise serializers.ValidationError(
                "Already subscribed to this user"
            )
        print('aboba1')
        return super().validate(data)


class BaseFavoriteShoppingCartSeralizer(serializers.ModelSerializer):
    class Meta:
        fields = ('recipe', 'author')
        read_only_fields = ('recipe', 'author')

    def validate(self, attrs):
        recipe_id = self.context.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        author = self.context.get('author')
        if self.Meta.model.objects.filter(
            recipe=recipe, author=author
        ).exists():
            raise serializers.ValidationError('The operation is already done')
        attrs['recipe'] = recipe
        attrs['author'] = author
        return attrs

    def to_representation(self, instance):
        return ShoppingCartFavouriteSerializerResponse(instance.recipe).data


class FavouriteSeriazlier(BaseFavoriteShoppingCartSeralizer):
    class Meta(BaseFavoriteShoppingCartSeralizer.Meta):
        model = Favourite


class ShoppingCartSerializer(BaseFavoriteShoppingCartSeralizer):
    class Meta(BaseFavoriteShoppingCartSeralizer.Meta):
        model = ShoppingCart


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = UserReadSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField('get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        'get_is_in_shopping_cart'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        print('aboba')
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Favourite.objects.filter(
                author=request.user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        print(request)
        return (
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                author=request.user, recipe=obj
            ).exists()
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        representation['ingredients'] = [
            {
                'id': recipe_ingredient.ingredient.id,
                'name': recipe_ingredient.ingredient.name,
                'measurement_unit': (
                    recipe_ingredient.ingredient.measurement_unit
                ),
                'amount': recipe_ingredient.amount,
            }
            for recipe_ingredient in instance.recipe_ingredients.all()
        ]
        print(representation)
        return representation


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, attrs):
        ingredient_data = attrs.get('recipe_ingredients')
        tag_data = attrs.get('tags')
        if not ingredient_data:
            raise serializers.ValidationError(
                {'ingredients': 'this field is required.'}
            )
        if not tag_data:
            raise serializers.ValidationError(
                {'tags': 'this field is required.'}
            )

        ingredient_ids = set()
        for ingredient in ingredient_data:
            if ingredient['id'] in ingredient_ids:
                raise serializers.ValidationError(
                    {'ingredients': 'ingredients should be unique'}
                )
            ingredient_ids.add(ingredient['id'])

        if not len(set(tag_data)) == len(tag_data):
            raise serializers.ValidationError(
                {'ingredients': 'ingredients should be unique'}
            )
        return attrs

    @staticmethod
    def create_recipe_ingredient_data(recipe, ingredients_data):
        recipe_ingredient_data = (
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data.get('amount', None),
            )
            for ingredient_data in ingredients_data
        )
        RecipeIngredient.objects.bulk_create(recipe_ingredient_data)

    @atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        request = self.context.get('request')
        validated_data['author'] = request.user
        recipe = Recipe.objects.create(**validated_data)

        self.create_recipe_ingredient_data(recipe, ingredients_data)

        recipe.tags.set(tags_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = validated_data.pop('tags', None)
        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_recipe_ingredient_data(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}
        ).data
