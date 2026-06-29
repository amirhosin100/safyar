from collections import Counter
from typing import Any, Iterator

from django.utils.translation import gettext_lazy as _
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer


# Use as parent of non-simple serializers
class BaseModelSerializer(ModelSerializer):

    @staticmethod
    def get_serializer_class(model):
        from apps.core.auto_generator.auto_generator import get_or_create_serializer

        simple_ser = get_or_create_serializer(model, "simple")
        if simple_ser is not None:
            return simple_ser
        return get_or_create_serializer(model, "full")

    @staticmethod
    def set_display_field(representation, instance, field_name) -> None | bool:
        try:
            get_display = getattr(instance, f"get_{field_name}_display")
            representation[f"{field_name}_display"] = get_display()
        except Exception:
            return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field_name, field in self.fields.items():
            self.set_display_field(representation, instance, field_name)
        representation["display_label"] = str(instance)

        return representation


class BaseSimpleSerializer(ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        operation = False
        if "request" in self.context and self.context["request"] is not None:
            if self.context["request"].GET.get("upper_obj", None) == "true":
                operation = True

        for field_name, field in self.fields.items():
            BaseModelSerializer.set_display_field(representation, instance, field_name)
            if not operation:
                continue

            if isinstance(field, (PrimaryKeyRelatedField, SerializerMethodField)):
                try:
                    related_instance = getattr(instance, field_name)
                except:
                    continue
                if (
                    related_instance
                    and not isinstance(related_instance, str)
                    and not isinstance(related_instance, int)
                ):
                    if "name" in representation or "title" in representation:
                        key = "name" if "name" in representation else "title"
                        representation[
                            key
                        ] += f' ({getattr(related_instance, "name", getattr(related_instance, "title", ""))})'
        representation["display_label"] = str(instance)
        return representation
