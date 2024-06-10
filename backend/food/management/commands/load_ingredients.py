import json

from django.conf import settings
from django.core.management.base import BaseCommand

from food.models import Ingredient

INGREDIENT_DATA_PATH = settings.BASE_DIR / 'data/ingredients.json'


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open(INGREDIENT_DATA_PATH, 'r') as file:
            data = json.load(file)
            ingredients = (
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit'],
                )
                for item in data
            )
            Ingredient.objects.bulk_create(ingredients)
