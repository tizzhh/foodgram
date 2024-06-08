from django.contrib import admin
from django.contrib.auth.models import Group

from .models import (Favourite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

admin.site.empty_value_display = 'нет данных'
admin.site.site_title = 'Админ-зона проекта Foodgram'
admin.site.site_header = 'Админ-зона проекта Foodgram'
admin.site.unregister(Group)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_display_links = ('name',)
    list_filter = ('name',)
    search_field = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('name',)
    list_filter = ('name',)
    search_field = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'author')
    list_filter = ('author',)
    search_field = ('author',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author')
    list_display_links = ('name', 'author')
    list_filter = ('name',)
    search_field = ('name',)


@admin.register(Favourite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'author')
    list_filter = ('author',)
    search_field = ('author',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient')
    list_filter = ('recipe',)
    search_field = ('recipe',)
