from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    FoodgramTokenObtainSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserUpdatePasswordSerializer,
)
from food.models import User


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
        'patch',
        'delete',
    )

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return UserReadSerializer
        return UserCreateSerializer

    @action(
        detail=False,
        methods=('get', 'patch'),
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
