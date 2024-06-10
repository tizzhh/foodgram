import os
import tempfile

import pyshorteners
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
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserAvatarSeriazlier, UserCreateSerializer,
                          UserReadSerializer, UserUpdatePasswordSerializer)
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


# class SubscriptionViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = SubscriptionSerializer
#     permission_classes = (IsAuthenticated,)
#     lookup_field = 'id'

#     def create(self, request, *args, **kwargs):
#         user_id_to_subscribe = self.kwargs.get('id')
#         user_to_subscribe = get_object_or_404(User, id=user_id_to_subscribe)
#         recipes_limit = request.query_params.get('recipes_limit')
#         serializer = SubscriptionSerializer(
#             user_to_subscribe,
#             data=request.data,
#             context={
#                 'user_id': user_id_to_subscribe,
#                 'user': request.user,
#                 'recipes_limit': recipes_limit,
#             },
#         )
#         serializer.is_valid(raise_exception=True)
#         request.user.is_subscribed.add(user_to_subscribe)
#         return Response(data=serializer.data, status=status.HTTP_201_CREATED)

#     def destroy(self, request, *args, **kwargs):
#         user_id_to_unsubscribe = self.kwargs.get('id')
#         user_to_unsubscribe = get_object_or_404(
#             User, id=user_id_to_unsubscribe
#         )
#         if not request.user.is_subscribed.filter(
#             id=user_id_to_unsubscribe
#         ).exists():
#             return Response(
#                 {'detail': 'Страница не найдена.'},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         request.user.is_subscribed.remove(user_to_unsubscribe)
#         return Response(status=status.HTTP_204_NO_CONTENT)


class FavouriteViewSet(BaseFavoriteShoppingCartViewSet):
    queryset = Favourite.objects.all()
    serializer_class = FavouriteSeriazlier
    # permission_classes = (IsAuthOrNotFound,)

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

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        cart_data = ShoppingCart.objects.filter(author=request.user)
        download_cart = {}
        for cart in cart_data:
            recipe = cart.recipe
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            for recipe_ingredient in recipe_ingredients:
                ingredient = recipe_ingredient.ingredient
                ingredient_amount = (
                    ingredient.name,
                    ingredient.measurement_unit,
                )
                ingredient_to_download_amount = download_cart.get(
                    ingredient_amount, 0
                )
                download_cart[ingredient_amount] = (
                    ingredient_to_download_amount + recipe_ingredient.amount
                )

        with tempfile.NamedTemporaryFile(
            delete=False, mode='w', encoding='utf-8'
        ) as tmp:
            path = tmp.name
            for name_measurement, amount in download_cart.items():
                tmp.write(
                    f'• {name_measurement[0]}'
                    f'({name_measurement[1]}) - {amount}\n'
                )

        with open(path, 'rb') as tmp:
            response = HttpResponse(tmp.read(), content_type='text/plain')
            response['Content-Disposition'] = (
                'attachment; filename=\'shopping_list.txt\''
            )

        os.remove(path)

        return response

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
    )
    def get_short_link(self, request, pk):
        s = pyshorteners.Shortener()
        short_url = s.tinyurl.short(request.get_full_path())
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


# class UserViewSet(DjoserUserViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserReadSerializer
#     permission_classes = [AllowAny]
#     http_method_names = ('get', 'post', 'put', 'delete',)

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         print(queryset)
#         return queryset

#     def get_permissions(self):
#         if '/me' in self.request.get_full_path():
#             return (IsAuthenticated(),)
#         return (AllowAny(),)

#     @action(
#         detail=False,
#         methods=('get',),
#         permission_classes=(IsAuthenticated,),
#         url_path='subscriptions',
#     )
#     def get_my_subscriptions(self, request):
#         subscribed_to_users = request.user.is_subscribed.all()
#         paginator = LimitOffsetPagination()
#         paginated_users = paginator.paginate_queryset(
#             subscribed_to_users, request
#         )
#         recipes_limit = request.query_params.get('recipes_limit')
#         serializer = SubscriptionSerializer(
#             paginated_users,
#             many=True,
#             context={
#                 'user_id': request.user.id,
#                 'user': request.user,
#                 'recipes_limit': recipes_limit,
#             },
#         )
#         return paginator.get_paginated_response(serializer.data)

#     @action(
#         detail=False,
#         methods=('put', 'delete'),
#         permission_classes=(IsAuthenticated,),
#         url_path='me/avatar',
#     )
#     def add_avatar(self, request):
#         if request.method == 'PUT':
#             seriazlier = UserAvatarSeriazlier(
#                 self.request.user, data=request.data
#             )
#             seriazlier.is_valid(raise_exception=True)
#             seriazlier.save()
#             return Response(data=seriazlier.data)
#         elif request.method == 'DELETE':
#             request.user.avatar.delete(save=True)
#             return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    http_method_names = (
        'get',
        'post',
        'put',
        'delete',
    )

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return UserReadSerializer
        return UserCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

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
        serializer = SubscriptionSerializer(
            paginated_users,
            many=True,
            context={
                'user_id': request.user.id,
                'user': request.user,
                'recipes_limit': recipes_limit,
            },
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def add_avatar(self, request):
        if request.method == 'PUT':
            seriazlier = UserAvatarSeriazlier(
                self.request.user, data=request.data
            )
            seriazlier.is_valid(raise_exception=True)
            seriazlier.save()
            return Response(data=seriazlier.data)
        elif request.method == 'DELETE':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='me',
    )
    def retrieve_me(self, request):
        serializer = UserReadSerializer(
            self.request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='set_password',
    )
    def update_password(self, request):
        serializer = UserUpdatePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['USER']
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(
            None,
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, pk):
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'subscription': pk},
            context={
                'recipes_limit': request.query_params.get('recipes_limit'),
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscription(self, request, pk):
        get_object_or_404(User, id=pk)
        deleted, _ = Subscribe.objects.filter(
            user=request.user.id, subscription=pk
        ).delete()
        print(deleted)
        if not deleted:
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
