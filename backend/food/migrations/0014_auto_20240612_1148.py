# Generated by Django 3.2.3 on 2024-06-12 11:48

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food', '0013_alter_recipeingredient_amount'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={
                'ordering': ('name', 'measurement_unit'),
                'verbose_name': 'Ингридиент',
                'verbose_name_plural': 'Ингридиенты',
            },
        ),
        migrations.AlterModelOptions(
            name='recipe',
            options={
                'ordering': ('created_at',),
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
            },
        ),
        migrations.AddField(
            model_name='recipe',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]