from django.contrib import admin
from django.contrib.auth.models import Group
from shortener import admin as sh_admin

from .models import Ingredient, Recipe, ShoppingCart, Tag, User

admin.site.empty_value_display = 'нет данных'
admin.site.site_title = 'Админ-зона проекта Foodgram'
admin.site.site_header = 'Админ-зона проекта Foodgram'
admin.site.unregister(Group)
admin.site.unregister(sh_admin.UrlMap)
admin.site.unregister(sh_admin.UrlProfile)


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
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'author')
    list_filter = ('author',)
    search_field = ('author',)
