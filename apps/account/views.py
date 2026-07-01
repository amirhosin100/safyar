import random

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
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
    UserUpdateSerializer,
    SendCodeResetPasswordSerializer,
    VerifyCodeSerializer, ResetPasswordSerializer, UserSerializer
)
from apps.core.base_classes.base_viewset import BaseAPIView
from apps.core.permissions import IsNotNormalUser
from apps.core.utils.jwt import get_tokens_for_user
from django.db import IntegrityError
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from apps.core.utils.prefix import verify_code


# TODO write tests
class UserLoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    @staticmethod
    def user_not_found():
        return Response(
            data={
                "error": _("username or password is incorrect")
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
                    "error": _("you cannot register, because you registered before.")
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SendCodeResetPasswordView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = SendCodeResetPasswordSerializer

    def post(self, request):
        serializer = SendCodeResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(national_code=serializer.validated_data["national_code"])
        except User.DoesNotExist:
            return Response(serializer.data)

        code = "".join(random.choices("0123456789", k=6))
        # TODO remove print and send a real sms
        print(code)
        national_code = user.national_code
        cache.set(verify_code.format(national_code=national_code), code, timeout=60)

        return Response(serializer.data)


class VerifyCodeView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = {"message": _("Password has been reset")}

        try:
            user = User.objects.get(national_code=serializer.validated_data["national_code"])
        except User.DoesNotExist:
            return Response(data)

        password = serializer.validated_data["password1"]
        user.set_password(password)
        user.save()
        return Response(data)


class UserListCreateView(BaseAPIView):
    permission_classes = (IsNotNormalUser,)
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
    permission_classes = (IsNotNormalUser,)
    serializer_class = UserUpdateSerializer

    @staticmethod
    def edit(request, user_id, partial):
        try:
            user = User.objects.get(branch=request.user.branch, user_id=user_id)
        except User.DoesNotExist:
            return Response(
                data={
                    "detail": _("user not found")
                },
                status=status.HTTP_404_NOT_FOUND
            )
        if request.user.user_type != UserTypeChoices.OWNER and user != request.user:
            return Response(
                data={
                    "detail":_("you don't have change this user")
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
                    "detail": _("user not found")
                },
                status=status.HTTP_404_NOT_FOUND
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserInformationView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
