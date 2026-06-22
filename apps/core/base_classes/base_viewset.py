
from django.db.models import ForeignKey, OneToOneField
from django.utils import translation

from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.core.utils.filters import (
    CustomFilterSetFilter,
    CustomGroupingFilter,
    CustomOrderingFilter,
    CustomSearchFilter,
)
from apps.core.utils.form_schema import build_form_schema
from apps.core.utils.pagination import OptionalPageNumberPagination
from apps.core.utils.i18n_request import negotiate_request_lang


class BaseAPIView(GenericAPIView):
    serializer_prefix = "Simple"
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_model_name = None
    ordering_fields = "__all__"
    filter_backends = [
        CustomFilterSetFilter,
        CustomSearchFilter,
        CustomOrderingFilter,
        CustomGroupingFilter,
    ]
    ordering = "-id"
    is_list = True

    def get_serializer_class(self):
        model = self.get_queryset().model
        from apps.core.auto_generator.auto_generator import get_or_create_serializer

        if self.is_list:
            serializer = get_or_create_serializer(model, "simple")
        else:
            serializer = get_or_create_serializer(model, "full")

        return serializer


class BaseProtectionViewSet(BaseAPIView, ModelViewSet):
    pagination_class = OptionalPageNumberPagination

    def get_serializer_class(self):
        model = super().get_queryset().model
        from apps.core.auto_generator.auto_generator import get_or_create_serializer

        if self.action == "list":
            simple_ser = get_or_create_serializer(model, "simple")
            if simple_ser is not None:
                return simple_ser
        elif self.action == "export_objects":
            return get_or_create_serializer(model, "export")
        elif self.action == "import_objects":
            return get_or_create_serializer(model, "full")
        elif self.action == "form_schema":
            return get_or_create_serializer(model, "full")
        return get_or_create_serializer(model, "full")

    @action(detail=False, methods=["get"], url_path="form-schema")
    def form_schema(self, request, *args, **kwargs):
        """
        Return field metadata for the create/update form of this resource.

        The schema is derived from the full ModelSerializer used by create and
        update, plus model meta information (verbose names, choices, related
        models). Frontend uses it to build a dynamic form.
        """
        model = super().get_queryset().model
        from apps.core.auto_generator.auto_generator import get_or_create_serializer

        serializer_class = get_or_create_serializer(model, "full")
        serializer = serializer_class(context=self.get_serializer_context())
        lang_code = negotiate_request_lang(request)
        with translation.override(lang_code):
            schema = build_form_schema(model, serializer)
        return Response(schema)

    def get_queryset(self):
        queryset = super().get_queryset()
        serializer_class = self.get_serializer_class()()  # create an instance
        fields = serializer_class.fields

        upper = self.request.GET.get("upper_obj", None) == "true"
        # step1, step2
        relation_fields_s1 = ()
        relation_fields_s2 = ()

        if self.action == "list":
            # FK + M2M expanded in list serializer; select/prefetch to avoid N+1.
            relation_fields_s1 = (ManyRelatedField, PrimaryKeyRelatedField)

        elif self.action == "retrieve":
            relation_fields_s1 = (PrimaryKeyRelatedField, ManyRelatedField)
            # if upper is false, we don't need FK,and,O2O
            if upper:
                relation_fields_s2 = (ForeignKey, OneToOneField)

        for field_name, field in fields.items():
            if isinstance(field, relation_fields_s1):
                if hasattr(field, "child_relation"):
                    # if field is be ManyToMany
                    sub_fields = field.child_relation.queryset.model._meta.fields
                    queryset = queryset.prefetch_related(field_name)
                else:
                    # Foreign key and OneToOne
                    sub_fields = field.queryset.model._meta.fields
                    queryset = queryset.select_related(field_name)

                sub_rel_fields = [
                    sub_field
                    for sub_field in sub_fields
                    if isinstance(sub_field, relation_fields_s2)
                ]
                for sub_rel_field in sub_rel_fields:
                    related = self.get_related(queryset, field, sub_rel_field)
                    queryset = related(field_name + "__" + sub_rel_field.name)

        return queryset


    @staticmethod
    def get_related(query_set, parent_field, sub_field):
        """
        checking if both fields is Foreign Key, it returns `select_related`
        else it returns `prefetch_related`
        FK -> FK = 'select_related'
        FK -> M = 'prefetch_related'
        M -> M = 'prefetch_related'
        M -> FK = 'prefetch_related'
        """
        if isinstance(parent_field, PrimaryKeyRelatedField) and isinstance(
            sub_field, (ForeignKey, OneToOneField)
        ):
            return query_set.select_related
        return query_set.prefetch_related
