from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views

api_v1_router = DefaultRouter()
api_v1_router.register('users', views.UserViewSet, basename='users')
api_v1_router.register('auth/token', views.FoodgramToken, basename='jwt-token')

urlpatterns = [
    path('', include(api_v1_router.urls)),
]
