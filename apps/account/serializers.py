from rest_framework import serializers

from apps.account.choices import UserTypeChoices
from apps.account.models import User, OwnerRequest
from apps.core.validations import phone_number_validator, national_code_validator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


class UserLoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "national_code",
            "password",
        )


class UserLoginResponseSerializer(serializers.ModelSerializer):
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

        if password1 != password2:
            raise serializers.ValidationError("Passwords don't match")

        try:
            validate_password(password1)
        except DjangoValidationError as e:
            raise serializers.ValidationError("please fix these %s" % str(e.messages))

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
