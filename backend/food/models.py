from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

MAX_NAME_LENGTH = 64
MAX_MEASUREMENT_LENGTH = 64


class Tag(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    slug = models.SlugField(unique=True, max_length=MAX_NAME_LENGTH)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    class MeasurementUnits(models.TextChoices):
        KG = "кг"
        GR = "г"
        ML = "мл"
        COOK_PREFERENCE = "по вкусу" "COOK'S PREFERENCE"

    name = models.CharField(max_length=MAX_NAME_LENGTH)
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_LENGTH,
        choices=MeasurementUnits.choices,
        default=MeasurementUnits.COOK_PREFERENCE,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self) -> str:
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField()
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

    class Meta:
        ordering = ('id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.name


class Favourite(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name='favourites', on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name='favourites', on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f'{self.recipe.name} is in favourites of {self.author.username}'

    class Meta:
        ordering = ('author',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'author'),
                name='unique-together-recipe-author-in-favorite',
            ),
        )


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name='shoppingcart', on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name='shoppingcart', on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return (
            f'{self.recipe.name} is in shopping cart of {self.author.username}'
        )

    class Meta:
        ordering = ('author',)
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'author'),
                name='unique-together-recipe-author-in-cart',
            ),
        )


class RecipeIngredient(models.Model):
    amount = models.SmallIntegerField()
    recipe = models.ForeignKey(
        Recipe, related_name='recipe_ingredients', on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, related_name='ingredient_recipes', on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f'Recipe {self.recipe.name} has the ingredient {self.ingredient.name} with an amount: {self.amount}'
