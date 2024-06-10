from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdminSettings

from food.models import User

admin.site.empty_value_display = 'нет данных'
admin.site.site_title = 'Админ-зона проекта Foodgram'
admin.site.site_header = 'Админ-зона проекта Foodgram'


@admin.register(User)
class UserAdmin(UserAdminSettings):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_display_links = ('username',)
    list_filter = ('username',)
    search_fields = ('username', 'email')
