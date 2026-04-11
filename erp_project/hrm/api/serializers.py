from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from hrm.models import (
    ZKDevice, AttendanceLog, DeviceUser, 
    DeviceCommand, OperationLog, DeviceHeartbeat,
    FingerprintTemplate, FaceTemplate
)


# ==================== DEVICE SERIALIZERS ====================

class ZKDeviceSerializer(serializers.ModelSerializer):
    online_status = serializers.SerializerMethodField()
    attendance_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ZKDevice
        fields = '__all__'
        
    def get_online_status(self, obj):
        if obj.last_activity:
            return (timezone.now() - obj.last_activity) < timedelta(minutes=5)
        return False
    
    def get_attendance_count(self, obj):
        return obj.attendance_logs.count()


class ZKDeviceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for device list"""
    online = serializers.SerializerMethodField()
    
    class Meta:
        model = ZKDevice
        fields = [
            'id', 'serial_number', 'device_name', 'device_type',
            'ip_address', 'is_active', 'is_online', 'last_activity', 
            'user_count', 'fp_count', 'face_count', 'transaction_count', 'online'
        ]
        
    def get_online(self, obj):
        if obj.last_activity:
            return (timezone.now() - obj.last_activity) < timedelta(minutes=5)
        return False


class ZKDeviceCreateSerializer(serializers.ModelSerializer):
    """Device registration serializer"""
    class Meta:
        model = ZKDevice
        fields = [
            'serial_number', 'device_name', 'device_type',
            'ip_address', 'mac_address', 'firmware_version',
            'platform', 'push_version', 'oem_vendor'
        ]


# ==================== ATTENDANCE SERIALIZERS ====================

class AttendanceLogSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    device_sn = serializers.CharField(source='device.serial_number', read_only=True)
    punch_type_display = serializers.CharField(source='get_punch_type_display', read_only=True)
    verify_type_display = serializers.CharField(source='get_verify_type_display', read_only=True)
    
    class Meta:
        model = AttendanceLog
        fields = [
            'id', 'device', 'device_name', 'device_sn',
            'user_id', 'punch_time', 'punch_type', 'punch_type_display',
            'verify_type', 'verify_type_display', 'work_code',
            'temperature', 'mask_status', 'is_synced', 'created_at'
        ]


class AttendanceLogCreateSerializer(serializers.Serializer):
    """Parse raw ADMS data"""
    PIN = serializers.CharField(max_length=50)
    CHECKTIME = serializers.DateTimeField(
        input_formats=['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S']
    )
    CHECKTYPE = serializers.IntegerField(required=False, default=0)
    VERIFYCODE = serializers.IntegerField(required=False, default=1)
    WORKCODE = serializers.CharField(required=False, default='', allow_blank=True)
    TEMPERATURE = serializers.DecimalField(
        required=False, max_digits=4, decimal_places=1, allow_null=True
    )
    MASKFLAG = serializers.IntegerField(required=False, default=0)


# ==================== MOBILE ATTENDANCE SERIALIZERS ====================

class MobileAttendanceSerializer(serializers.Serializer):
    """Mobile attendance check-in/check-out"""
    user_id = serializers.CharField(max_length=50)
    punch_type = serializers.ChoiceField(choices=[(0, 'Check In'), (1, 'Check Out')])
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, required=False, allow_null=True)
    location_accuracy = serializers.FloatField(required=False, allow_null=True)
    
    def validate(self, data):
        """Validate location if provided"""
        if data.get('latitude') and data.get('longitude'):
            # Check if location is within allowed range
            lat = float(data['latitude'])
            lon = float(data['longitude'])
            
            if not (-90 <= lat <= 90):
                raise serializers.ValidationError("Invalid latitude value")
            if not (-180 <= lon <= 180):
                raise serializers.ValidationError("Invalid longitude value")
        
        return data
    
    def create(self, validated_data):
        """Create attendance log from mobile"""
        from hrm.models import ZKDevice
        
        # Get or create a virtual mobile device
        mobile_device, _ = ZKDevice.objects.get_or_create(
            serial_number='MOBILE_APP',
            defaults={
                'device_name': 'Mobile App',
                'device_type': 'mobile',
                'connection_type': 'tcp',
                'is_active': True,
            }
        )
        
        # Create attendance log
        attendance_log = AttendanceLog.objects.create(
            device=mobile_device,
            user_id=validated_data['user_id'],
            punch_time=timezone.now(),
            punch_type=validated_data['punch_type'],
            verify_type=0,  # Password/Mobile
            source='mobile',
            latitude=validated_data.get('latitude'),
            longitude=validated_data.get('longitude'),
            location_accuracy=validated_data.get('location_accuracy'),
        )
        
        return attendance_log


class MobileAttendanceResponseSerializer(serializers.ModelSerializer):
    """Response for mobile attendance"""
    punch_type_display = serializers.CharField(source='get_punch_type_display', read_only=True)
    
    class Meta:
        model = AttendanceLog
        fields = [
            'id', 'user_id', 'punch_time', 'punch_type', 'punch_type_display',
            'latitude', 'longitude', 'location_accuracy', 'created_at'
        ]


# ==================== DEVICE USER SERIALIZERS ====================

class DeviceUserSerializer(serializers.ModelSerializer):
    privilege_display = serializers.CharField(source='get_privilege_display', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = DeviceUser
        fields = '__all__'


class DeviceUserCreateSerializer(serializers.Serializer):
    """Create/Update device user"""
    PIN = serializers.CharField(max_length=50)
    Name = serializers.CharField(max_length=100, required=False, default='')
    Pri = serializers.IntegerField(required=False, default=0)
    Passwd = serializers.CharField(required=False, default='', allow_blank=True)
    Card = serializers.CharField(required=False, default='', allow_blank=True)
    Grp = serializers.CharField(required=False, default='1')


# ==================== COMMAND SERIALIZERS ====================

class DeviceCommandSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    command_type_display = serializers.CharField(source='get_command_type_display', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = DeviceCommand
        fields = '__all__'


class DeviceCommandCreateSerializer(serializers.Serializer):
    """Create device command"""
    device_id = serializers.IntegerField()
    command_type = serializers.ChoiceField(choices=DeviceCommand.COMMAND_TYPES)
    command_content = serializers.CharField(required=False, default='', allow_blank=True)


class BulkCommandSerializer(serializers.Serializer):
    """Send command to multiple devices"""
    device_ids = serializers.ListField(child=serializers.IntegerField())
    command_type = serializers.ChoiceField(choices=DeviceCommand.COMMAND_TYPES)
    command_content = serializers.CharField(required=False, default='', allow_blank=True)


# ==================== OPERATION LOG SERIALIZERS ====================

class OperationLogSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    
    class Meta:
        model = OperationLog
        fields = '__all__'


# ==================== HEARTBEAT SERIALIZERS ====================

class DeviceHeartbeatSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = DeviceHeartbeat
        fields = '__all__'


# ==================== TEMPLATE SERIALIZERS ====================

class FingerprintTemplateSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = FingerprintTemplate
        exclude = ['template_data']


class FaceTemplateSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = FaceTemplate
        exclude = ['template_data']


# ==================== REPORT SERIALIZERS ====================

class AttendanceReportSerializer(serializers.Serializer):
    """Daily attendance report"""
    user_id = serializers.CharField()
    user_name = serializers.CharField(required=False, allow_blank=True)
    date = serializers.DateField()
    first_punch = serializers.DateTimeField(required=False, allow_null=True)
    last_punch = serializers.DateTimeField(required=False, allow_null=True)
    total_hours = serializers.FloatField(required=False, default=0)
    punch_count = serializers.IntegerField()
    status = serializers.CharField(required=False, default='present')


class DeviceStatsSerializer(serializers.Serializer):
    """Device statistics"""
    total_devices = serializers.IntegerField()
    online_devices = serializers.IntegerField()
    offline_devices = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_logs_today = serializers.IntegerField()
    total_logs_month = serializers.IntegerField()
