# Generated by Django 3.2.3 on 2024-06-10 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food', '0009_auto_20240605_1002'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipeingredient',
            options={
                'verbose_name': 'Рецепт-ингредиент',
                'verbose_name_plural': 'Рецепты-ингредиенты',
            },
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='measurement_unit',
            field=models.CharField(max_length=64),
        ),
    ]
