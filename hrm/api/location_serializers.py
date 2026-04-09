from rest_framework import serializers


class MobileCheckinSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    accuracy = serializers.FloatField(required=False, allow_null=True)
    punch_type = serializers.IntegerField(default=0)
    punch_time = serializers.DateTimeField(required=False, allow_null=True)
