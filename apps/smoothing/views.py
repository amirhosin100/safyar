from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.base_classes.base_viewset import BaseProtectionViewSet, FilterByBranchViewSet
from apps.core.permissions import IsSuperUser, IsNotNormalUser, HasBranch
from apps.smoothing.models import Smoothing, Branch, Colleague
from apps.smoothing.serializers import SmoothingSerializer, BranchSerializer , ColleagueSerializer


# TODO write tests for these
class SmoothingViewSet(BaseProtectionViewSet):
    serializer_class = SmoothingSerializer
    queryset = Smoothing.objects.all()
    permission_classes = (IsSuperUser,)


class BranchViewSet(BaseProtectionViewSet):
    serializer_class = BranchSerializer
    permission_classes = (HasBranch & IsNotNormalUser,)
    queryset = Branch.objects.all()

    def perform_create(self, serializer):
        smoothing = self.request.user.branch.smoothing
        serializer.save(smoothing=smoothing)

    def get_queryset(self):
        return self.queryset.filter(smoothing=self.request.user.branch.smoothing)


class ColleagueViewSet(FilterByBranchViewSet):
    serializer_class = ColleagueSerializer
    permission_classes = (HasBranch | IsSuperUser,)
    queryset = Colleague.objects.all()


class SmoothingAPIView(APIView):
    """
    for editing smoothing in settings
    """
    permission_classes = (IsNotNormalUser,)
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
        return self.edit(request, partial=False)

    def patch(self, request):
        return self.edit(request, partial=True)


class BranchAPIView(APIView):
    """
    for editing branch in settings
    """
    permission_classes = (IsNotNormalUser,)
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
        return self.edit(request, partial=False)

    def patch(self, request):
        return self.edit(request, partial=True)
