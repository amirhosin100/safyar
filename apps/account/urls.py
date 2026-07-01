from django.urls import path
from apps.account.views import (
    UserLoginView,
    UserRegisterView,
    UserListCreateView,
    UserUpdateDeleteView,
    UserInformationView,
    SendCodeResetPasswordView,
    ResetPasswordView,
    VerifyCodeView
)

app_name = "account"

urlpatterns = [
    path("account/login/", UserLoginView.as_view(), name="login"),
    path("account/register/", UserRegisterView.as_view(), name="register"),

    path("account/users/", UserListCreateView.as_view(), name="user-list-create"),
    path("account/user/<int:user_id>/", UserUpdateDeleteView.as_view(), name="user-delete-update"),

    path("account/info/", UserInformationView.as_view(), name="user-info"),
    path("account/verify/", VerifyCodeView.as_view(), name="verify-code"),
    path("account/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("account/send-sms/", SendCodeResetPasswordView.as_view(), name="send-sms"),
]
