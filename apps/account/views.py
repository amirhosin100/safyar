from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.account.models import User
from apps.account.serializers import UserLoginSerializer, UserLoginResponseSerializer, UserRegisterSerializer
from apps.core.utils.jwt import get_tokens_for_user
from django.db import IntegrityError


class UserLoginView(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def user_not_found():
        return Response(
            data={
                "error": "username or password is incorrect"
            },
            status=status.HTTP_404_NOT_FOUND
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
        return Response(res_serializer.data, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    permission_classes = (AllowAny,)

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