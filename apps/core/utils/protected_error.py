from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import ValidationError


def show_protected_error(e):
    try:
        ref_obj = list(e.protected_objects)[0]
        if hasattr(ref_obj, "title"):
            obj_title = ref_obj.title
        elif hasattr(ref_obj, "name"):
            obj_title = ref_obj.name
        else:
            obj_title = ref_obj.id

        connected_obj_name = f"{ref_obj._meta.verbose_name} ( {obj_title} )"
        return Response(
            data={
                "detail": _(
                    "selected object because of connection to {connected_obj_name} can not be deleted"
                ).format(connected_obj_name=connected_obj_name)
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as exc:
        raise ValidationError(str(exc))
