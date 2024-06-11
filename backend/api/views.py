import pyshorteners
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientSearch, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavouriteSeriazlier, IngredientSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          ShoppingCartSerializer, SubscriptionReadSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserAvatarSeriazlier)
from food.models import (Favourite, Ingredient, Recipe, RecipeIngredient,
                         ShoppingCart, Tag, User)
from foodgram_user.models import Subscribe


class BaseFavoriteShoppingCartViewSet(viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = (IsAuthorOrReadOnly,)
    lookup_field = 'recipe_id'

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        serializer = self.get_serializer(
            data=self.request.data,
            context={'recipe_id': recipe_id, 'user': self.request.user},
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.validated_data['recipe']
        serializer.save(author=self.request.user, recipe=recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class FavouriteViewSet(BaseFavoriteShoppingCartViewSet):
    queryset = Favourite.objects.all()
    serializer_class = FavouriteSeriazlier

    def destroy(self, request, *args, **kwargs):
        recipe_id_to_delete = self.kwargs.get('recipe_id')
        recipe_to_delete = get_object_or_404(Recipe, id=recipe_id_to_delete)
        if not (
            item := request.user.favourites.filter(recipe=recipe_to_delete)
        ).exists():
            return Response(
                {'detail': 'recipe is missing from favourites'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(BaseFavoriteShoppingCartViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer

    def destroy(self, request, *args, **kwargs):
        recipe_id_to_delete = self.kwargs.get('recipe_id')
        recipe_to_delete = get_object_or_404(Recipe, id=recipe_id_to_delete)
        if not (
            item := request.user.shoppingcart.filter(recipe=recipe_to_delete)
        ).exists():
            return Response(
                {'detail': 'recipe is missing from shopping cart'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeReadSerializer
        return RecipeSerializer

    @staticmethod
    def create_return_cart_file(queryset):
        shopping_cart_file_contents = ''
        for cart_data in queryset:
            shopping_cart_file_contents += (
                f'• {cart_data["ingredient__name"]}'
                f'({cart_data["ingredient__measurement_unit"]}) - {cart_data["total_amount"]}\n'
            )

        response = HttpResponse(
            shopping_cart_file_contents, content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename=\'shopping_list.txt\''
        )

        return response

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        cart_data = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__author=request.user
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('amount'))
        )

        return self.create_return_cart_file(cart_data)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
    )
    def get_short_link(self, request, pk):
        shortener = pyshorteners.Shortener()
        short_url = shortener.tinyurl.short(request.get_full_path())
        return Response({'short-link': short_url})


class BaseTagIngredientViewSet(viewsets.ModelViewSet):
    http_method_names = ('get',)
    pagination_class = None


class TagViewSet(BaseTagIngredientViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(BaseTagIngredientViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearch


class UserViewSet(DjoserUserViewSet):
    http_method_names = (
        'get',
        'post',
        'put',
        'delete',
    )

    def get_permissions(self):
        if '/me' in self.request.get_full_path():
            return (IsAuthenticated(),)
        return (AllowAny(),)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def get_my_subscriptions(self, request):
        subscribed_to_users = request.user.is_subscribed.all()
        paginator = LimitOffsetPagination()
        paginated_users = paginator.paginate_queryset(
            subscribed_to_users, request
        )
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = SubscriptionReadSerializer(
            paginated_users,
            many=True,
            context={
                'recipes_limit': recipes_limit,
            },
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def add_avatar(self, request):
        seriazlier = UserAvatarSeriazlier(self.request.user, data=request.data)
        seriazlier.is_valid(raise_exception=True)
        seriazlier.save()
        return Response(data=seriazlier.data)

    @add_avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'subscription': id},
            context={
                'recipes_limit': request.query_params.get('recipes_limit'),
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscription(self, request, id):
        get_object_or_404(User, id=id)
        deleted, _ = Subscribe.objects.filter(
            user=request.user.id, subscription=id
        ).delete()
        print(deleted)
        if not deleted:
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
