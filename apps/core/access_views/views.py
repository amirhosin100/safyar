from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.translation import gettext_lazy as _

from apps.core.access_views.code import get_identify
from apps.core.access_views.serializers import CodeSerializer


@extend_schema(request=CodeSerializer)
class AccessView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = None
    queryset = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.check_attrs()
        self.object_id = None

    def _set_object_id(self, object_id):
        self.object_id = object_id

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.check_code(request)

    def check_code(self, request):
        identify_code = request.data.get("identify_code", None)
        if identify_code is None:
            raise ValidationError(_("identify_code is required"))

        got, result = get_identify(identify_code)
        if got is False:
            raise ValidationError(result)

        self._set_object_id(result)

    def check_attrs(self):
        if self.queryset is None:
            raise ValueError("you have to set queryset")
        if self.serializer_class is None:
            raise ValueError("you have to set serializer_class")

    def post(self, request):
        try:
            project = self.queryset.get(id=self.object_id)
        except self.queryset.model.DoesNotExist:
            return Response(
                {"detail": _(f"{self.queryset.model.__name__} not found")},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(project)

        return Response(data=serializer.data)
