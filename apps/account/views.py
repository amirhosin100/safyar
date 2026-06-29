from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.account.choices import UserTypeChoices
from apps.account.models import User
from apps.account.serializers import (
    UserLoginSerializer,
    UserLoginResponseSerializer,
    UserRegisterSerializer,
    UserCreationSerializer,
    UserDetailSerializer,
    UserUpdateSerializer, CaptchaSerializer
)
from apps.core.base_classes.base_viewset import BaseAPIView
from apps.core.permissions import IsAdminOrOwner
from apps.core.utils.jwt import get_tokens_for_user
from django.db import IntegrityError
from apps.core.captcha import Captcha


# TODO write tests
class UserLoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    @staticmethod
    def user_not_found():
        return Response(
            data={
                "error": "username or password is incorrect"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    @extend_schema(
        request=UserLoginSerializer,
        responses=UserLoginResponseSerializer
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        national_code = serializer.validated_data["national_code"]
        try:
            user = User.objects.get(national_code=national_code)
        except User.DoesNotExist:
            return self.user_not_found()

        if not user.check_password(serializer.validated_data["password"]) or not user.is_active:
            return self.user_not_found()

        tokens = get_tokens_for_user(user)
        res_serializer = UserLoginResponseSerializer(data=tokens)
        return Response(res_serializer.initial_data, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.create(serializer.validated_data)
        except IntegrityError:
            return Response(
                data={
                    "error": "you cannot register, because you registered before."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreateCaptchaView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        data = Captcha.create_captcha()
        serializer = CaptchaSerializer(data=data)

        return Response(serializer.initial_data, status=status.HTTP_201_CREATED)


class UserListCreateView(BaseAPIView):
    permission_classes = (IsAdminOrOwner,)
    serializer_class = UserDetailSerializer
    queryset = User.objects.filter(user_type__in=[UserTypeChoices.NORMAL, UserTypeChoices.ADMIN])

    def post(self, request):
        serializer = UserCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.create(serializer.validated_data)

        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

    def get(self, request):
        users = self.queryset.filter(branch=request.user.branch)
        serializer = UserDetailSerializer(users, many=True)

        return Response(serializer.data)


class UserUpdateDeleteView(APIView):
    permission_classes = (IsAdminOrOwner,)
    serializer_class = UserUpdateSerializer

    @staticmethod
    def edit(request, user_id, partial):
        try:
            user = User.objects.get(branch=request.user.branch, user_id=user_id)
        except User.DoesNotExist:
            return Response(
                data={
                    "detail": "user not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        if request.user.user_type != UserTypeChoices.OWNER and user != request.user:
            return Response(
                data={
                    "you don't have change this user"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserUpdateSerializer(data=request.data, instance=user, partial=partial)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, user_id):
        return self.edit(request, user_id, False)

    def patch(self, request, user_id):
        return self.edit(request, user_id, True)

    def delete(self, request, user_id):
        try:
            user = User.objects.get(branch=request.user.branch, user_id=user_id)
        except User.DoesNotExist:
            return Response(
                data={
                    "detail": "user not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
