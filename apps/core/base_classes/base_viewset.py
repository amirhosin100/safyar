from django.utils import translation

from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import HasBranch, IsSuperUser
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


class BaseProtectionViewSet(BaseAPIView, ModelViewSet):
    pagination_class = OptionalPageNumberPagination

    def get_serializer_class(self):
        model = super().get_queryset().model
        from apps.core.auto_generator.auto_generator import get_or_create_serializer

        if self.action == "list":
            simple_ser = get_or_create_serializer(model, "simple")
            if simple_ser is not None:
                return simple_ser
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



class FilterByBranchViewSet(BaseProtectionViewSet):
    permission_classes = (IsSuperUser | HasBranch,)
    branch_prefix = "branch"

    def get_queryset(self):
        return self.queryset.filter(**{self.branch_prefix: self.request.user.active_branch})
