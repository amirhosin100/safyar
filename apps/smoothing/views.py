from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.base_classes.base_viewset import BaseProtectionViewSet
from apps.core.permissions import IsSuperUser, IsAdminOrOwner
from apps.smoothing.models import Smoothing
from apps.smoothing.serializers import SmoothingSerializer, BranchSerializer


# TODO write tests for these
class SmoothingSuperUserViewSet(BaseProtectionViewSet):
    serializer_class = SmoothingSerializer
    queryset = Smoothing.objects.all()
    permission_classes = (IsSuperUser,)


class SmoothingAPIView(APIView):
    permission_classes = (IsAdminOrOwner,)
    serializer_class = SmoothingSerializer

    @staticmethod
    def edit(request, partial):
        smoothing = request.user.branch.smoothing

        serializer = SmoothingSerializer(instance=smoothing, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def get(self, request):
        smoothing = request.user.branch.smoothing
        serializer = SmoothingSerializer(instance=smoothing)
        return Response(serializer.data)

    def put(self, request):
        self.edit(request, partial=False)

    def patch(self, request):
        self.edit(request, partial=True)


class BranchAPIView(APIView):
    permission_classes = (IsAdminOrOwner,)
    serializer_class = BranchSerializer

    @staticmethod
    def edit(request, partial):
        branch = request.user.branch

        serializer = BranchSerializer(instance=branch, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def get(self, request):
        branch = request.user.branch
        serializer = BranchSerializer(instance=branch)
        return Response(serializer.data)

    def put(self, request):
        self.edit(request, partial=False)

    def patch(self, request):
        self.edit(request, partial=True)
