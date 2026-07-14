from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.account.choices import UserTypeChoices
from apps.account.models import User
from apps.core.permissions import HasBranch, IsNotNormalUser, IsSuperUser
from apps.costumer.models import Car, Costumer
from apps.project.choices import ProjectStatusChoices
from apps.project.models import Project
from apps.report.serializers import (
    BranchCarCountSerializer,
    SmoothingWalletTransactionReportSerializer,
    SmoothingUserReportSerializer,
    BranchColleagueReportSerializer,
    GlobalReportSerializer,
    BranchCostumerReportSerializer,
    SmoothingBranchReportSerializer,
)
from apps.smoothing.choices import JobTypeChoices
from apps.smoothing.models import Branch, Colleague, Smoothing
from apps.wallet.choices import TransactionTypeChoices
from apps.wallet.models import WalletTransaction


class BranchCarCountView(APIView):
    """
    Total number of cars belonging to the current user's active_branch.
    """
    permission_classes = (HasBranch,)
    serializer_class = BranchCarCountSerializer

    def get(self, request):
        branch = request.user.active_branch
        car_count = Car.objects.filter(costumer__branch=branch).count()

        serializer = self.serializer_class({"car_count": car_count})
        return Response(serializer.data)


class SmoothingWalletTransactionReportView(APIView):
    """
    Total / deposit / withdraw transaction counts for the smoothing
    the user's active_branch belongs to.
    """
    permission_classes = (HasBranch, IsNotNormalUser)
    serializer_class = SmoothingWalletTransactionReportSerializer

    def get(self, request):
        smoothing = request.user.active_branch.smoothing

        counts = WalletTransaction.objects.filter(wallet__smoothing=smoothing).aggregate(
            total_transactions=Count("id"),
            total_settles=Count(
                "id", filter=Q(transaction_type=TransactionTypeChoices.SETTLE)
            ),
            total_withdraws=Count(
                "id", filter=Q(transaction_type=TransactionTypeChoices.WITHDRAW)
            ),
        )

        serializer = self.serializer_class(counts)
        return Response(serializer.data)


class SmoothingUserReportView(APIView):
    """
    Total / admin / normal user counts for the smoothing the
    user's active_branch belongs to.
    """
    permission_classes = (HasBranch, IsNotNormalUser)
    serializer_class = SmoothingUserReportSerializer

    def get(self, request):
        smoothing = request.user.active_branch.smoothing

        counts = User.objects.filter(active_branch__smoothing=smoothing).aggregate(
            total_users=Count("id"),
            total_admin_users=Count(
                "id", filter=Q(user_type=UserTypeChoices.ADMIN)
            ),
            total_normal_users=Count(
                "id", filter=Q(user_type=UserTypeChoices.NORMAL)
            ),
        )

        serializer = self.serializer_class(counts)
        return Response(serializer.data)


class BranchColleagueReportView(APIView):
    """
    Total colleague counts (smoother/painter/masker) for the
    user's active_branch.
    """
    permission_classes = (HasBranch, IsNotNormalUser)
    serializer_class = BranchColleagueReportSerializer

    def get(self, request):
        branch = request.user.active_branch

        counts = Colleague.objects.filter(branch=branch).aggregate(
            total_colleagues=Count("id"),
            total_smoothers=Count(
                "id", filter=Q(job_type=JobTypeChoices.SMOOTHER)
            ),
            total_painters=Count(
                "id", filter=Q(job_type=JobTypeChoices.PAINTER)
            ),
            total_maskers=Count(
                "id", filter=Q(job_type=JobTypeChoices.MASKER)
            ),
        )

        serializer = self.serializer_class(counts)
        return Response(serializer.data)


class GlobalReportView(APIView):
    """
    System-wide report: total users and total smoothings.
    Only accessible by superusers.
    """
    permission_classes = (IsSuperUser,)
    serializer_class = GlobalReportSerializer

    def get(self, request):
        data = {
            "total_users": User.objects.count(),
            "total_smoothings": Smoothing.objects.count(),
        }

        serializer = self.serializer_class(data)
        return Response(serializer.data)


class BranchCostumerReportView(APIView):
    """
    Total / active costumer counts, plus today's SUBMITTED project count
    for the user's active_branch.
    """
    permission_classes = (HasBranch,)
    serializer_class = BranchCostumerReportSerializer

    def get(self, request):
        branch = request.user.active_branch
        today = timezone.localdate()

        total_costumers = Costumer.objects.filter(branch=branch).count()

        # TODO: define what an "active" costumer means and implement the real query
        active_costumers = 0

        today_submissions = Project.objects.filter(
            branch=branch,
            status=ProjectStatusChoices.SUBMITTED,
            created_at__date=today,
        ).count()

        data = {
            "total_costumers": total_costumers,
            "active_costumers": active_costumers,
            "today_submissions": today_submissions,
        }

        serializer = self.serializer_class(data)
        return Response(serializer.data)


class SmoothingBranchReportView(APIView):
    """
    Total / active branch counts for the smoothing the user's
    active_branch belongs to.
    """
    permission_classes = (HasBranch, IsNotNormalUser)
    serializer_class = SmoothingBranchReportSerializer

    def get(self, request):
        smoothing = request.user.active_branch.smoothing

        total_branches = Branch.objects.filter(smoothing=smoothing).count()

        # TODO: define what an "active" branch means and implement the real query
        active_branches = 0

        data = {
            "total_branches": total_branches,
            "active_branches": active_branches,
        }

        serializer = self.serializer_class(data)
        return Response(serializer.data)