from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef
from django.db.models.query import QuerySet

from food import constants

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        unique=True, max_length=constants.MAX_TAG_NAME_LENGTH
    )
    slug = models.SlugField(
        unique=True, max_length=constants.MAX_TAG_SLUG_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=constants.MAX_INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        max_length=constants.MAX_MEASUREMENT_LENGTH,
    )

    class Meta:
        ordering = ('name', 'measurement_unit')
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique-name-measurement_unit',
            ),
        )
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self) -> str:
        return f'{self.name}, {self.measurement_unit}'


class RecipeQuerySet(QuerySet):
    def get_is_favorited_is_in_shopping_cart(self, request_user):
        if request_user.is_authenticated:
            self = self.annotate(
                is_favorited=Exists(
                    Favourite.objects.filter(
                        author=request_user, recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        author=request_user, recipe=OuterRef('pk')
                    )
                ),
            )
        else:
            self = self.annotate(
                is_favorited=Exists(Favourite.objects.none()),
                is_in_shopping_cart=Exists(ShoppingCart.objects.none()),
            )
        return self


class Recipe(models.Model):
    name = models.CharField(max_length=constants.MAX_RECIPE_NAME_LENGTH)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                constants.MIN_COOKING_TIME,
                'Время готовки не может быть меньше 1 минуты',
            ),
            MaxValueValidator(
                constants.MAX_COOKING_TIME,
                'Время готовки не может быть больше 24 часов',
            ),
        )
    )
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient'
    )
    image = models.ImageField(
        upload_to='api/images/', null=True, default=None, blank=True
    )
    author = models.ForeignKey(
        User, related_name='recipes', on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.name


class RecipeAuthorBaseModel(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Favourite(RecipeAuthorBaseModel):
    class Meta:
        ordering = ('author',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favourites'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'author'),
                name='unique-together-recipe-author-in-favorite',
            ),
        )

    def __str__(self) -> str:
        return f'{self.recipe.name} is in favourites of {self.author.username}'


class ShoppingCart(RecipeAuthorBaseModel):
    class Meta:
        ordering = ('author',)
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        default_related_name = 'shoppingcart'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'author'),
                name='unique-together-recipe-author-in-cart',
            ),
        )

    def __str__(self) -> str:
        return (
            f'{self.recipe.name} is in shopping cart of {self.author.username}'
        )


class RecipeIngredient(models.Model):
    amount = models.SmallIntegerField(
        validators=(
            MinValueValidator(
                constants.MIN_INGREDIENT_AMOUNT,
                'Количество ингридиента не может быть меньше 1',
            ),
            MaxValueValidator(
                constants.MAX_INGREDIENT_AMOUNT,
                'Количество ингридиента не может быть больше 8192',
            ),
        )
    )
    recipe = models.ForeignKey(
        Recipe, related_name='recipe_ingredients', on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, related_name='ingredient_recipes', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Рецепт-ингредиент'
        verbose_name_plural = 'Рецепты-ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique-together-recipe-ingredient',
            ),
        )

    def __str__(self) -> str:
        return (
            f'Recipe {self.recipe.name} has the ingredient '
            f'{self.ingredient.name} with an amount: {self.amount}'
        )
