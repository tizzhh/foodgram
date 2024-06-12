from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.fields import Base64ImageField
from food.models import (Favourite, Ingredient, Recipe, RecipeIngredient,
                         ShoppingCart, Tag, User)
from foodgram_user.models import Subscribe


class UserAvatarSeriazlier(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


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
        request = self.context.get('request', None)
        return (
            request is not None
            and request.user.is_authenticated
            and Subscribe.objects.filter(
                user=request.user, subscription=obj
            ).exists()
        )


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
        validators = (
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'subscription'),
            ),
        )

    def to_representation(self, instance):
        return SubscriptionReadSerializer(
            instance.subscription, context=self.context
        ).data

    def validate(self, data):
        user = data['user']
        subscription = data['subscription']
        if user == subscription:
            raise serializers.ValidationError("Cannot subscribe to yourself")
        return super().validate(data)


class BaseFavoriteShoppingCartSeralizer(serializers.ModelSerializer):
    class Meta:
        fields = ('recipe', 'author')

    def validate(self, attrs):
        recipe = attrs.get('recipe')
        author = attrs.get('author')
        if self.Meta.model.objects.filter(
            recipe=recipe, author=author
        ).exists():
            raise serializers.ValidationError('The operation is already done')
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


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients', many=True
    )
    tags = TagSerializer(many=True)
    author = UserReadSerializer(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
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
            instance.ingredients.clear()
            self.create_recipe_ingredient_data(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}
        ).data
