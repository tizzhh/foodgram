# Generated by Django 3.2.3 on 2024-06-10 20:16

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food', '0012_auto_20240610_0955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.SmallIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(
                        1, 'Количество ингридиента не может быть меньше 1'
                    ),
                    django.core.validators.MaxValueValidator(
                        8192,
                        'Количество ингридиента не может быть больше 8192',
                    ),
                ]
            ),
        ),
    ]