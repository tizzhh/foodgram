from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views

api_v1_router = DefaultRouter()
# api_v1_router.register(
#     r'recipes/(?P<recipe_id>\d+)/shopping_cart',
#     views.ShoppingCartViewSet,
#     basename='shopping_cart',
# ) # по какой-то причине такой подход с http_method_names, включающий в себя
# delete дает 405 на delete
api_v1_router.register('users', views.UserViewSet, basename='users')
api_v1_router.register('tags', views.TagViewSet, basename='tags')
api_v1_router.register(
    'ingredients', views.IngredientViewSet, basename='ingredients'
)
api_v1_router.register('recipes', views.RecipeViewSet, basename='recipes')
api_v1_router.register('ingredients', views.RecipeViewSet, basename='recipes')

urlpatterns = [
    path(
        'recipes/<int:recipe_id>/shopping_cart/',
        views.ShoppingCartViewSet.as_view(
            {'post': 'create', 'delete': 'destroy'}
        ),
        name='shopping_cart',
    ),
    path(
        'recipes/<int:recipe_id>/favorite/',
        views.FavouriteViewSet.as_view(
            {'post': 'create', 'delete': 'destroy'}
        ),
        name='favorite',
    ),
    path('', include(api_v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
