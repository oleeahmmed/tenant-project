# ==================== zktest/admin/zkdeviceadmin.py ====================
"""
ZKDevice Admin with Unified Smart Actions
Auto-detects device type (ADMS/TCP) and uses appropriate method
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta

from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from unfold.contrib.filters.admin import (
    RangeDateTimeFilter,
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)

from hrm.models import (
    ZKDevice, AttendanceLog, DeviceUser, 
    DeviceCommand, OperationLog, DeviceHeartbeat,
    FingerprintTemplate, FaceTemplate, TCPSyncLog
)


# ==================== INLINE CLASSES ====================

class DeviceUserInline(TabularInline):
    model = DeviceUser
    extra = 0
    fields = ('user_id', 'name', 'privilege', 'has_fingerprint', 'has_face', 'is_active')
    readonly_fields = ('has_fingerprint', 'has_face')
    show_change_link = True
    tab = True


class DeviceCommandInline(TabularInline):
    model = DeviceCommand
    extra = 0
    fields = ('command_type', 'status', 'created_at', 'executed_at')
    readonly_fields = ('created_at', 'executed_at')
    show_change_link = True
    max_num = 10
    tab = True


# ==================== ZK DEVICE ADMIN ====================

@admin.register(ZKDevice)
class ZKDeviceAdmin(ModelAdmin):
    list_display = (
        'serial_number', 'device_name', 'ip_address', 
        'display_connection_type', 'display_online_status',
        'user_count', 'transaction_count', 'last_activity'
    )
    list_filter = (
        'is_active', 
        'is_online',
        ('connection_type', ChoicesDropdownFilter),
        ('device_type', ChoicesDropdownFilter),
        ('last_activity', RangeDateTimeFilter),
    )
    search_fields = ('serial_number', 'device_name', 'ip_address', 'mac_address')
    list_editable = ('device_name',)
    ordering = ('-last_activity',)
    readonly_fields = ('registered_at', 'last_activity', 'created_at', 'updated_at')
    list_per_page = 25
    inlines = [DeviceUserInline, DeviceCommandInline]
    
    fieldsets = (
        ('Device Information', {
            'fields': (
                ('serial_number', 'device_name'),
                ('device_type', 'connection_type'),
                ('oem_vendor',),
            ),
            'classes': ['tab'],
        }),
        ('Network Configuration', {
            'fields': (
                ('ip_address', 'mac_address'),
                ('port', 'tcp_timeout', 'tcp_password'),
            ),
            'classes': ['tab'],
        }),
        ('Status', {
            'fields': (
                ('is_active', 'is_online'),
                ('last_activity', 'registered_at'),
            ),
            'classes': ['tab'],
        }),
        ('Statistics', {
            'fields': (
                ('user_count', 'fp_count'),
                ('face_count', 'transaction_count'),
            ),
            'classes': ['tab'],
        }),
    )
    
    # ==================== SIMPLIFIED ACTIONS ====================
    actions = [
        'sync_users',
        'sync_attendance',
        'reboot_devices',
        'sync_time',
        'mark_offline'
    ]
    
    # ==================== DISPLAY METHODS ====================
    
    @display(description='Connection', label={
        'adms': 'success',
        'tcp': 'info',
        'both': 'warning'
    })
    def display_connection_type(self, obj):
        return obj.connection_type
    
    @display(description='Status', label={
        True: 'success',
        False: 'danger'
    })
    def display_online_status(self, obj):
        if obj.last_activity:
            is_online = (timezone.now() - obj.last_activity) < timedelta(minutes=5)
            return is_online
        return False
    
    # ==================== SMART SYNC ACTIONS ====================
    
    @action(description="🔄 Sync Users (Auto-detect)")
    def sync_users(self, request, queryset):
        """
        Smart sync: Auto-detects device connection type
        - TCP devices: Immediate fetch via PyZK
        - ADMS devices: Queue command
        - Both: Try TCP first, fallback to ADMS
        """
        tcp_count = 0
        adms_count = 0
        error_count = 0
        total_imported = 0
        
        for device in queryset:
            try:
                if device.connection_type in ['tcp', 'both']:
                    # TCP DEVICE - Pull via PyZK immediately
                    if not device.ip_address:
                        error_count += 1
                        continue
                    
                    from hrm.utils import import_users_from_device, auto_create_employee_from_device_user
                    
                    result = import_users_from_device(device)
                    
                    if result.get('success'):
                        tcp_count += 1
                        total_imported += result.get('imported', 0)
                        
                        # Auto-create employees
                        if result.get('imported', 0) > 0:
                            new_users = DeviceUser.objects.filter(device=device)
                            for du in new_users:
                                auto_create_employee_from_device_user(du)
                    else:
                        # If TCP fails and device supports both, try ADMS
                        if device.connection_type == 'both':
                            DeviceCommand.objects.create(
                                device=device,
                                command_type='GET_USERS'
                            )
                            adms_count += 1
                        else:
                            error_count += 1
                            
                else:
                    # ADMS DEVICE - Queue command
                    DeviceCommand.objects.create(
                        device=device,
                        command_type='GET_USERS'
                    )
                    adms_count += 1
                    
            except Exception as e:
                error_count += 1
        
        # Show results
        messages = []
        if tcp_count > 0:
            messages.append(f"✅ TCP: {tcp_count} devices, {total_imported} users imported")
        if adms_count > 0:
            messages.append(f"📤 ADMS: {adms_count} commands queued")
        if error_count > 0:
            messages.append(f"⚠️ {error_count} failed")
        
        self.message_user(request, ' | '.join(messages) if messages else "No devices processed")
    
    @action(description="🔄 Sync Attendance (Auto-detect)")
    def sync_attendance(self, request, queryset):
        """
        Smart sync: Auto-detects device connection type
        - TCP devices: Immediate fetch via PyZK
        - ADMS devices: Queue command
        - Both: Try TCP first, fallback to ADMS
        """
        tcp_count = 0
        adms_count = 0
        error_count = 0
        total_imported = 0
        
        for device in queryset:
            try:
                if device.connection_type in ['tcp', 'both']:
                    # TCP DEVICE - Pull via PyZK immediately
                    if not device.ip_address:
                        error_count += 1
                        continue
                    
                    from hrm.utils import import_attendance_from_device
                    
                    result = import_attendance_from_device(device)
                    
                    if result.get('success'):
                        tcp_count += 1
                        total_imported += result.get('imported', 0)
                    else:
                        # If TCP fails and device supports both, try ADMS
                        if device.connection_type == 'both':
                            DeviceCommand.objects.create(
                                device=device,
                                command_type='GET_LOGS'
                            )
                            adms_count += 1
                        else:
                            error_count += 1
                            
                else:
                    # ADMS DEVICE - Queue command
                    DeviceCommand.objects.create(
                        device=device,
                        command_type='GET_LOGS'
                    )
                    adms_count += 1
                    
            except Exception as e:
                error_count += 1
        
        # Show results
        messages = []
        if tcp_count > 0:
            messages.append(f"✅ TCP: {tcp_count} devices, {total_imported} records imported")
        if adms_count > 0:
            messages.append(f"📤 ADMS: {adms_count} commands queued")
        if error_count > 0:
            messages.append(f"⚠️ {error_count} failed")
        
        self.message_user(request, ' | '.join(messages) if messages else "No devices processed")
    
    # ==================== BASIC ACTIONS ====================
    
    @action(description="🔄 Reboot Devices")
    def reboot_devices(self, request, queryset):
        """Works for both device types"""
        count = 0
        for device in queryset:
            if device.connection_type in ['tcp', 'both'] and device.ip_address:
                # Try TCP restart
                try:
                    from hrm.utils import execute_device_command
                    execute_device_command(device, 'REBOOT')
                    count += 1
                except:
                    # Fallback to ADMS if TCP fails
                    DeviceCommand.objects.create(device=device, command_type='REBOOT')
                    count += 1
            else:
                # Queue ADMS command
                DeviceCommand.objects.create(device=device, command_type='REBOOT')
                count += 1
        
        self.message_user(request, f"Reboot command sent to {count} devices")
    
    @action(description="🕐 Sync Time")
    def sync_time(self, request, queryset):
        """Works for both device types"""
        count = 0
        for device in queryset:
            if device.connection_type in ['tcp', 'both'] and device.ip_address:
                # Try TCP time sync
                try:
                    from hrm.utils import execute_device_command
                    execute_device_command(device, 'UPDATE_TIME')
                    count += 1
                except:
                    # Fallback to ADMS if TCP fails
                    DeviceCommand.objects.create(device=device, command_type='UPDATE_TIME')
                    count += 1
            else:
                # Queue ADMS command
                DeviceCommand.objects.create(device=device, command_type='UPDATE_TIME')
                count += 1
        
        self.message_user(request, f"Time sync command sent to {count} devices")
    
    @action(description="❌ Mark as Offline")
    def mark_offline(self, request, queryset):
        queryset.update(is_online=False)
        self.message_user(request, f"{queryset.count()} devices marked as offline")



# ==================== ATTENDANCE LOG ADMIN ====================

@admin.register(AttendanceLog)
class AttendanceLogAdmin(ModelAdmin):
    list_display = (
        'user_id', 'display_device', 'punch_time', 
        'display_punch_type', 'display_verify_type',
        'display_location', 'display_sync_status', 'created_at'
    )
    list_filter = (
        'user_id',
        'source',
        ('punch_time', RangeDateTimeFilter),
    )
    search_fields = ('user_id',)
    ordering = ('-punch_time',)
    readonly_fields = ('raw_data', 'created_at', 'synced_at', 'display_map_link')
    date_hierarchy = 'punch_time'
    list_per_page = 50
    
    fieldsets = (
        ('Attendance Info', {
            'fields': (
                ('user_id', 'device'),
                ('punch_time', 'punch_type'),
                ('verify_type', 'work_code'),
                ('source',),
            ),
        }),
        ('Location Info', {
            'fields': (
                ('latitude', 'longitude'),
                ('location_accuracy',),
                ('display_map_link',),
            ),
            'classes': ('collapse',),
        }),
        ('Additional Info', {
            'fields': (
                ('temperature', 'mask_status'),
                ('is_synced', 'synced_at'),
                ('raw_data',),
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': (
                ('created_at',),
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_as_synced', 'mark_as_unsynced']
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number
    
    @display(description='Punch', label={
        0: 'success',
        1: 'warning'
    })
    def display_punch_type(self, obj):
        return obj.punch_type
    
    @display(description='Verify', label='info')
    def display_verify_type(self, obj):
        return obj.get_verify_type_display()
    
    @display(description='Location')
    def display_location(self, obj):
        if obj.latitude and obj.longitude:
            return format_html('📍 <a href="https://www.google.com/maps?q={},{}" target="_blank">View Map</a>', 
                             obj.latitude, obj.longitude)
        return '-'
    
    @display(description='Map Link')
    def display_map_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://www.google.com/maps?q={},{}" target="_blank" style="padding: 8px 16px; background: #4285f4; color: white; text-decoration: none; border-radius: 4px;">🗺️ Open in Google Maps</a><br><br>'
                '<small>Lat: {}, Lon: {}, Accuracy: {}m</small>',
                obj.latitude, obj.longitude,
                obj.latitude, obj.longitude, obj.location_accuracy or 'N/A'
            )
        return 'No location data'
    
    @display(description='Synced', label={
        True: 'success',
        False: 'warning'
    })
    def display_sync_status(self, obj):
        return obj.is_synced
    
    @action(description="Mark as Synced")
    def mark_as_synced(self, request, queryset):
        queryset.update(is_synced=True, synced_at=timezone.now())
        self.message_user(request, f"{queryset.count()} records marked as synced")
    
    @action(description="Mark as Unsynced")
    def mark_as_unsynced(self, request, queryset):
        queryset.update(is_synced=False, synced_at=None)
        self.message_user(request, f"{queryset.count()} records marked as unsynced")


# ==================== DEVICE USER ADMIN ====================

@admin.register(DeviceUser)
class DeviceUserAdmin(ModelAdmin):
    list_display = (
        'user_id', 'name', 'display_device', 
        'display_employee_status', 'display_biometrics', 'is_active'
    )
    list_filter = (
        ('device', RelatedDropdownFilter),
        'is_active',
        'has_fingerprint',
        'has_face',
    )
    search_fields = ('user_id', 'name', 'card_number', 'device__device_name')
    list_editable = ('is_active',)
    ordering = ('device', 'user_id')
    list_per_page = 50
    
    actions = ['activate_users', 'deactivate_users', 'create_employees']
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number
    
    @display(description='Employee', label={
        True: 'success',
        False: 'warning'
    })
    def display_employee_status(self, obj):
        return obj.get_employee() is not None
    
    @display(description='Biometrics')
    def display_biometrics(self, obj):
        icons = []
        if obj.has_fingerprint:
            icons.append('👆 FP')
        if obj.has_face:
            icons.append('😊 Face')
        return ' | '.join(icons) if icons else '-'
    
    @action(description="Activate Users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} users activated")
    
    @action(description="Deactivate Users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} users deactivated")
    
    @action(description="Create Employee Records")
    def create_employees(self, request, queryset):
        from hrm.utils import auto_create_employee_from_device_user
        created_count = 0
        for user in queryset:
            emp = auto_create_employee_from_device_user(user)
            if emp:
                created_count += 1
        self.message_user(request, f"{created_count} employee records created")


# ==================== DEVICE COMMAND ADMIN ====================

@admin.register(DeviceCommand)
class DeviceCommandAdmin(ModelAdmin):
    list_display = (
        'id', 'display_device', 'command_type', 
        'display_status', 'created_at', 'executed_at'
    )
    list_filter = (
        ('device', RelatedDropdownFilter),
        ('command_type', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
    )
    search_fields = ('device__serial_number', 'command_content')
    ordering = ('-created_at',)
    list_per_page = 50
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number
    
    @display(description='Status', label={
        'pending': 'warning',
        'sent': 'info',
        'executed': 'success',
        'failed': 'danger',
    })
    def display_status(self, obj):
        return obj.status


# ==================== OPERATION LOG ADMIN ====================

@admin.register(OperationLog)
class OperationLogAdmin(ModelAdmin):
    list_display = ('display_device', 'operation_type', 'admin_id', 'operation_time')
    list_filter = (
        ('device', RelatedDropdownFilter),
        ('operation_type', ChoicesDropdownFilter)
    )
    search_fields = ('device__device_name', 'admin_id', 'user_id')
    ordering = ('-operation_time',)
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number


# ==================== DEVICE HEARTBEAT ADMIN ====================

@admin.register(DeviceHeartbeat)
class DeviceHeartbeatAdmin(ModelAdmin):
    list_display = ('display_device', 'heartbeat_time', 'ip_address', 'user_count')
    list_filter = (('device', RelatedDropdownFilter),)
    ordering = ('-heartbeat_time',)
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number


# ==================== FINGERPRINT TEMPLATE ADMIN ====================

@admin.register(FingerprintTemplate)
class FingerprintTemplateAdmin(ModelAdmin):
    list_display = ('user_id', 'display_device', 'finger_index', 'template_size')
    list_filter = (('device', RelatedDropdownFilter),)
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number


# ==================== FACE TEMPLATE ADMIN ====================

@admin.register(FaceTemplate)
class FaceTemplateAdmin(ModelAdmin):
    list_display = ('user_id', 'display_device', 'face_index', 'template_size')
    list_filter = (('device', RelatedDropdownFilter),)
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number


# ==================== TCP SYNC LOG ADMIN ====================

@admin.register(TCPSyncLog)
class TCPSyncLogAdmin(ModelAdmin):
    list_display = (
        'display_device', 'sync_type', 'display_status',
        'records_found', 'records_synced', 'records_failed',
        'started_at', 'completed_at'
    )
    list_filter = (
        ('device', RelatedDropdownFilter),
        ('sync_type', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('started_at', RangeDateTimeFilter),
    )
    search_fields = ('device__device_name', 'device__serial_number', 'error_message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'started_at', 'completed_at')
    list_per_page = 50
    
    fieldsets = (
        ('Sync Information', {
            'fields': (
                ('device', 'sync_type'),
                ('status',),
            ),
            'classes': ['tab'],
        }),
        ('Statistics', {
            'fields': (
                ('records_found', 'records_synced'),
                ('records_failed',),
            ),
            'classes': ['tab'],
        }),
        ('Error Details', {
            'fields': (
                ('error_message',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('started_at', 'completed_at'),
                ('created_at',),
            ),
            'classes': ['tab'],
        }),
    )
    
    @display(description='Device')
    def display_device(self, obj):
        return obj.device.device_name or obj.device.serial_number
    
    @display(description='Status', label={
        'pending': 'warning',
        'running': 'info',
        'completed': 'success',
        'failed': 'danger',
    })
    def display_status(self, obj):
        return obj.status
