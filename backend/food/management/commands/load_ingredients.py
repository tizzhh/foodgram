import json

from django.core.management.base import BaseCommand

from food.models import Ingredient

INGREDIENT_DATA_PATH = '/app/data/ingredients.json'


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open(INGREDIENT_DATA_PATH, 'r') as file:
            data = json.load(file)
            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit'],
                )
