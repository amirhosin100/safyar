from rest_framework import serializers


class BranchCarCountSerializer(serializers.Serializer):
    car_count = serializers.IntegerField(read_only=True)


class SmoothingWalletTransactionReportSerializer(serializers.Serializer):
    total_transactions = serializers.IntegerField(read_only=True)
    total_settles = serializers.IntegerField(read_only=True)
    total_withdraws = serializers.IntegerField(read_only=True)


class SmoothingUserReportSerializer(serializers.Serializer):
    total_users = serializers.IntegerField(read_only=True)
    total_admin_users = serializers.IntegerField(read_only=True)
    total_normal_users = serializers.IntegerField(read_only=True)


class BranchColleagueReportSerializer(serializers.Serializer):
    total_colleagues = serializers.IntegerField(read_only=True)
    total_smoothers = serializers.IntegerField(read_only=True)
    total_painters = serializers.IntegerField(read_only=True)
    total_maskers = serializers.IntegerField(read_only=True)


class GlobalReportSerializer(serializers.Serializer):
    total_users = serializers.IntegerField(read_only=True)
    total_smoothings = serializers.IntegerField(read_only=True)


class BranchCostumerReportSerializer(serializers.Serializer):
    total_costumers = serializers.IntegerField(read_only=True)
    active_costumers = serializers.IntegerField(read_only=True)
    today_submissions = serializers.IntegerField(read_only=True)


class SmoothingBranchReportSerializer(serializers.Serializer):
    total_branches = serializers.IntegerField(read_only=True)
    active_branches = serializers.IntegerField(read_only=True)