from django.urls import path
from .views import (
    RegisterDeviceAPIView,
    DeviceTokenListAPIView,
    DeviceTokenDeactivateAPIView,
    SendTestNotificationAPIView
)

app_name = 'notifications'

urlpatterns = [
    # FCM token registration API
    path('devices/register/', RegisterDeviceAPIView.as_view(), name='register_device'),
    
    # List user's registered devices
    path('devices/', DeviceTokenListAPIView.as_view(), name='device_list'),
    
    # Deactivate device token
    path('devices/<int:pk>/deactivate/', DeviceTokenDeactivateAPIView.as_view(), name='deactivate_device'),
    
    # Send test notification (only used during development)
    path('test-notification/', SendTestNotificationAPIView.as_view(), name='test_notification'),
] 