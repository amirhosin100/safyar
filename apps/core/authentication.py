from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication, AuthUser
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import Token

from django.utils.translation import gettext_lazy as _


class JWTAuthentication(BaseJWTAuthentication):
    def get_user(self, validated_token: Token) -> AuthUser:
        user = super().get_user(validated_token)

        if not user.is_active_smoothing:
            raise AuthenticationFailed(_("your smoothing is deactivated"), code="user_inactive")

        return user
