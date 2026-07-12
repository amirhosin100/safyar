from django.db import IntegrityError
from rest_framework import status, serializers
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView

from apps.core.base_classes.base_viewset import FilterByBranchViewSet
from apps.costumer.serializers import CostumerSerializer, CarSerializer, AddCostumerSerializer

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


class AddCostumerView(APIView):
    serializer_class = AddCostumerSerializer

    def post(self, request):
        serializer = AddCostumerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch_id = serializer.validated_data['branch']
        phone_number = serializer.validated_data['phone_number']
        try:
            costumer = Costumer.objects.get(
                branch__id=branch_id,
                phone_number=phone_number
            )
        except Costumer.DoesNotExist:
            costumer = Costumer.objects.create(
                phone_number=phone_number,
                branch__id=branch_id,
                name=serializer.validated_data['costumer_name'],
                gender=serializer.validated_data['gender'],
                address=serializer.validated_data['address'],
            )
        Car.objects.create(
            costumer=costumer,
            name=serializer.validated_data['car_name'],
            plate=serializer.validated_data['plate'],
            color=serializer.validated_data['color'],
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)