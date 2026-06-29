from django.urls import path
from apps.account.views import (
    UserLoginView,
    UserRegisterView,
    UserListCreateView,
    UserUpdateDeleteView,
    CreateCaptchaView
)

app_name = "account"

urlpatterns = [
    path("account/login/", UserLoginView.as_view(), name="login"),
    path("account/register/", UserRegisterView.as_view(), name="register"),
    path("account/create-captcha/", CreateCaptchaView.as_view(), name="create-captcha"),

    path("account/users/", UserListCreateView.as_view(), name="user-list-create"),
    path("account/user/<int:user_id>/", UserUpdateDeleteView.as_view(), name="user-delete-update"),
]
