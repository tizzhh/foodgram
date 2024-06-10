# Generated by Django 3.2.3 on 2024-06-10 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food', '0011_auto_20240610_0949'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='favourite',
            options={
                'default_related_name': 'favourites',
                'ordering': ('author',),
                'verbose_name': 'Избранное',
                'verbose_name_plural': 'Избранное',
            },
        ),
        migrations.AlterModelOptions(
            name='shoppingcart',
            options={
                'default_related_name': 'shoppingcart',
                'ordering': ('author',),
                'verbose_name': 'Корзина покупок',
                'verbose_name_plural': 'Корзины покупок',
            },
        ),
        migrations.RemoveConstraint(
            model_name='ingredient',
            name='unique_name_measurement_unit',
        ),
        migrations.AddConstraint(
            model_name='ingredient',
            constraint=models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique-name-measurement_unit',
            ),
        ),
        migrations.AddConstraint(
            model_name='recipeingredient',
            constraint=models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique-together-recipe-ingredient',
            ),
        ),
    ]
