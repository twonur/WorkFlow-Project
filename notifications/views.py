from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import DeviceToken
from .serializers import DeviceTokenSerializer
from .fcm import send_push_notification, send_multicast_notification
import logging

logger = logging.getLogger(__name__)

class RegisterDeviceAPIView(generics.CreateAPIView):
    """
    API endpoint for saving FCM token.
    Saves FCM tokens coming from Flutter application.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceTokenSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context

class DeviceTokenListAPIView(generics.ListAPIView):
    """
    Lists user's registered device tokens.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceTokenSerializer
    
    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user, is_active=True)

class DeviceTokenDeactivateAPIView(generics.DestroyAPIView):
    """
    Deactivates device token.
    Token is not completely deleted, only set to inactive state.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SendTestNotificationAPIView(APIView):
    """
    API endpoint for sending test notification.
    Used to test notification system during development.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """
        Sends test notification to all user's active devices.
        """
        user = request.user
        tokens = DeviceToken.objects.filter(
            user=user, 
            is_active=True
        ).values_list('token', flat=True)
        
        if not tokens:
            return Response(
                {"detail": "Kayıtlı aktif cihaz bulunamadı."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        title = "Test Bildirimi"
        body = f"Merhaba {user.username}, bu bir test bildirimidir!"
        
        # Send notification to all devices in token list
        result = send_multicast_notification(
            list(tokens), 
            title, 
            body,
            {"type": "test_notification"}
        )
        
        return Response({
            "detail": "Test bildirimi gönderildi",
            "success_count": result["success"],
            "failure_count": result["failure"]
        })
