from rest_framework import status
from rest_framework.response import Response

from apps.core.base_classes.base_viewset import FilterByBranchViewSet, BaseProtectionViewSet
from apps.core.permissions import HasBranch
from apps.costumer.serializers import CostumerSerializer, CarSerializer

from apps.costumer.models import Costumer, Car


class CostumerViewSet(FilterByBranchViewSet):
    serializer_class = CostumerSerializer
    queryset = Costumer.objects.all()


class CarViewSet(BaseProtectionViewSet):
    serializer_class = CarSerializer
    queryset = Car.objects.all()
    permission_classes = (HasBranch,)

    def get_queryset(self):
        return self.queryset.filter(costumer__branch=self.request.user.branch)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        costumer_id = serializer.validated_data['costumer']
        costumer = Costumer.objects.get(costumer_id=costumer_id)
        if request.user.branch != costumer.branch:
            return Response(
                data={"error": "You don't have permission to create car for this customer."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
