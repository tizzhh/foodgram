import django_filters
from django_filters import rest_framework as filters

from food.models import Recipe


class RecipeFilter(filters.FilterSet):
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
