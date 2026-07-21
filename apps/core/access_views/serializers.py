from rest_framework import serializers


class CodeSerializer(serializers.Serializer):
    identify_code = serializers.CharField()