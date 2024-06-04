import os

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from shortener import shortener

from .serializers import (
    FoodgramTokenObtainSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserUpdatePasswordSerializer,
)
from food.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User,
)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'recipe_id'

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        serializer = ShoppingCartSerializer(
            data=self.request.data,
            context={'recipe_id': recipe_id, 'user': self.request.user},
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.validated_data['recipe']
        serializer.save(author=self.request.user, recipe=recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    http_method_names = ('get', 'post', 'patch')

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

        print(download_cart)
        path = "tmp.txt"
        try:
            with open(path, 'a+') as tmp:
                for name_measurement, amount in download_cart.items():
                    tmp.write(
                        f'• {name_measurement[0]} ({name_measurement[1]}) - {amount}\n'
                    )
                response = HttpResponse(tmp, content_type='text/plain')
                response['Content-Disposition'] = (
                    'attachment; filename="Список покупок"'
                )
                return response
        finally:
            os.remove(path)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
    )
    def get_short_link(self, request, pk):
        original_url = request.get_full_path()
        short_link = shortener.create(request.user.id, original_url)
        return Response({'short-link': short_link})


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ('get',)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class FoodgramToken(viewsets.GenericViewSet):
    @action(
        detail=False,
        methods=('post',),
        url_path='login',
    )
    def login_token(self, request):
        serializer = FoodgramTokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = serializer.get_token(serializer.validated_data['USER'])
        return Response(
            {
                'auth_token': str(access_token),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='logout',
    )
    def logout_token(self, request):
        serializer = FoodgramTokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


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
        if request.method == 'PATCH':
            serializer.save()
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
