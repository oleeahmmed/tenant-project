from rest_framework import serializers


class PyZKUserFetchSerializer(serializers.Serializer):
    import_new = serializers.BooleanField(default=True)
    auto_create_employees = serializers.BooleanField(default=True)


class PyZKAttendanceFetchSerializer(serializers.Serializer):
    date_range = serializers.ChoiceField(
        choices=["today", "7days", "30days", "month", "custom"],
        default="today",
    )
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    user_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    import_new = serializers.BooleanField(default=True)
