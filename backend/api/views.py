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
    TagSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserUpdatePasswordSerializer,
)
from food.models import Ingredient, Recipe, ShoppingCart, Tag, User


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
        print(cart_data)

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
