import base64

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import AccessToken

from food.models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User,
)


class UserUpdatePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate(self, attrs):
        request = self.context.get('request')
        user = get_object_or_404(User, email=request.user.email)
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError('Incorrect password')
        attrs['USER'] = user
        return attrs


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return obj.subscribers.exists()

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


class UserCreateSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('password')
        data['id'] = instance.id
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


class FoodgramTokenObtainSerializer(TokenObtainSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['username']
        self.fields['email'] = serializers.EmailField()

    @classmethod
    def get_token(cls, user):
        return AccessToken.for_user(user)

    def validate(self, attrs):
        password = attrs['password']
        email = attrs['email']
        user = get_object_or_404(User, email=email)
        if not user.check_password(password) or email != user.email:
            raise serializers.ValidationError(
                'Incorrect password and/or email'
            )
        attrs['USER'] = user
        return attrs


class ShoppingCartFavouriteSerializerResponse(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = ShoppingCartFavouriteSerializerResponse(
        many=True, read_only=True
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
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
        read_only_fields = (
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

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def validate(self, attrs):
        user_id_to_subscribe = self.context.get('user_id')
        user_to_subscribe = get_object_or_404(User, id=user_id_to_subscribe)

        user_that_subscribes = self.context.get('user')
        if user_id_to_subscribe == user_that_subscribes.id:
            raise serializers.ValidationError('Cannot subscribe to oneself')
        if user_that_subscribes.is_subscribed.filter(
            id=user_to_subscribe.id
        ).exists():
            raise serializers.ValidationError('Already subscribed')

        attrs['user_to_subscribe'] = user_to_subscribe
        return attrs

    def to_representation(self, instance):
        user = self.context.get('user')
        representation = super().to_representation(instance)
        representation['is_subscribed'] = user.is_subscribed.filter(
            id=instance.id
        ).exists()
        return representation


class BaseFavoriteShoppingCartSeralizer(serializers.ModelSerializer):
    model = None

    def validate(self, attrs):
        recipe_id = self.context.get('recipe_id')
        recipe = Recipe.objects.get(id=recipe_id)
        if self.model.objects.filter(
            recipe=recipe, author=self.context.get('user')
        ).exists():
            raise serializers.ValidationError('The operation is already done')
        attrs['recipe'] = recipe
        return attrs

    def to_representation(self, instance):
        return ShoppingCartFavouriteSerializerResponse(instance.recipe).data

    class Meta:
        fields = ('recipe', 'author')
        read_only_fields = ('recipe', 'author')


class FavouriteSeriazlier(BaseFavoriteShoppingCartSeralizer):
    model = Favourite

    class Meta(BaseFavoriteShoppingCartSeralizer.Meta):
        model = Favourite


class ShoppingCartSerializer(BaseFavoriteShoppingCartSeralizer):
    model = ShoppingCart

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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = UserReadSerializer(read_only=True)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        request = self.context.get('request')
        validated_data['author'] = request.user
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data['id'].id
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data.get('amount', None),
            )

        recipe.tags.set(tags_data)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)

        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = validated_data.pop('tags', None)
        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                ingredient = get_object_or_404(
                    Ingredient, id=ingredient_data['id'].id
                )
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient_data.get('amount', None),
                )

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        representation['ingredients'] = [
            {
                'id': recipe_ingredient.ingredient.id,
                'name': recipe_ingredient.ingredient.name,
                'measurement_unit': recipe_ingredient.ingredient.measurement_unit,
                'amount': recipe_ingredient.amount,
            }
            for recipe_ingredient in instance.recipe_ingredients.all()
        ]
        return representation

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time',
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
