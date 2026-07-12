from django.db import IntegrityError
from rest_framework import status, serializers
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from apps.core.base_classes.base_viewset import FilterByBranchViewSet
from apps.costumer.serializers import CostumerSerializer, CarSerializer

from apps.costumer.models import Costumer, Car


class CostumerViewSet(FilterByBranchViewSet):
    serializer_class = CostumerSerializer
    queryset = Costumer.objects.prefetch_related("cars")

    def perform_create(self, serializer):
        branch = self.request.user.active_branch
        try:
            serializer.save(branch=branch)
        except IntegrityError as e:
            raise serializers.ValidationError({'detail': _("phone_number and branch must be unique together")})


class CarViewSet(FilterByBranchViewSet):
    serializer_class = CarSerializer
    queryset = Car.objects.all()
    branch_prefix = "costumer__branch"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        costumer = serializer.validated_data['costumer']
        self.check_object_permissions(request, costumer)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
