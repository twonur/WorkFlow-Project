from django.contrib import admin
from .models import DeviceToken

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'token')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
