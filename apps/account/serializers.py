from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.account.choices import UserTypeChoices
from apps.account.models import User, OwnerRequest
from apps.core.validations import phone_number_validator, national_code_validator, password_validator, \
    validate_verify_code
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.smoothing.models import Branch


class UserLoginSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    national_code = serializers.CharField(
        max_length=10,
        validators=[national_code_validator],
    )


class UserLoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class UserRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    national_code = serializers.CharField(max_length=10, validators=[national_code_validator])
    phone_number = serializers.CharField(max_length=11, validators=[phone_number_validator])
    address = serializers.CharField()
    shop_name = serializers.CharField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password1 = attrs.get('password1')
        password2 = attrs.get('password2')

        password_validator(password1, password2)

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            full_name=validated_data.get('full_name'),
            national_code=validated_data.get('national_code'),
            phone_number=validated_data.get('phone_number'),
            user_type=UserTypeChoices.OWNER,
            is_active=False,
        )
        user.set_password(validated_data.get('password1'))
        user.save()
        OwnerRequest.objects.create(user=user)

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    active_branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=True
    )
    class Meta:
        model = User
        fields = [
            "full_name",
            "national_code",
            "phone_number",
            "user_type",
            "allowed_branches",
            "active_branch",
        ]


class UserCreationSerializer(UserDetailSerializer):
    password = serializers.CharField(
        required=True,
        write_only=True
    )

    class Meta:
        model = User
        fields = UserDetailSerializer.Meta.fields + ["password"]

    def validate_user_type(self, user_type):
        if user_type not in (UserTypeChoices.ADMIN, UserTypeChoices.NORMAL):
            raise ValidationError(
                _("you can use these %s %s") % (UserTypeChoices.ADMIN.value, UserTypeChoices.NORMAL.value)
            )
        return user_type

    def validate_password(self, password):
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError(_("please fix these %s") % str(e.messages))

        return password

    def create(self, validated_data):
        user = User(
            full_name=validated_data["full_name"],
            active_branch=validated_data["active_branch"],
            national_code=validated_data["national_code"],
            phone_number=validated_data["phone_number"],
            user_type=validated_data["user_type"],
        )
        user.set_password(validated_data["password"])
        user.save()

        return user


class UserUpdateSerializer(UserCreationSerializer):
    password = serializers.CharField(
        required=False,
        write_only=True
    )

    def save(self, **kwargs):
        password = self.validated_data.pop("password", None)
        if password:
            self.instance.set_password(password)
        super().save(**kwargs)


class SendCodeResetPasswordSerializer(serializers.Serializer):
    national_code = serializers.CharField(
        max_length=10, validators=[national_code_validator]
    )
    message = serializers.CharField(
        read_only=True,
        default=_("Verification code has been sent")
    )


class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, write_only=True)
    national_code = serializers.CharField(max_length=10, validators=[national_code_validator])

    def validate(self, attrs):
        code = attrs.get('code')
        national_code = attrs.get('national_code')

        validate_verify_code(national_code, code)
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    national_code = serializers.CharField(max_length=10, validators=[national_code_validator])
    code = serializers.CharField(max_length=6, write_only=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password1 = attrs.get('password1')
        password2 = attrs.get('password2')
        national_code = attrs.get('national_code')
        code = attrs.get('code')

        validate_verify_code(national_code, code)
        password_validator(password1, password2)

        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password", "groups", "user_permissions"]
