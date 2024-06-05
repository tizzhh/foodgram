import django_filters
from django.db.models import Q

from food.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(field_name='tags__slug')
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(favourites__author=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(shoppingcart__author=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )


class IngredientSearch(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_by_name')

    def filter_by_name(self, queryset, name, value):
        if not value:
            return queryset

        results = queryset.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).all()
        return results

    class Meta:
        model = Ingredient
        fields = ('name',)
