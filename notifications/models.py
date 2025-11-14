from django.db import models
from django.conf import settings

# Create your models here.

class DeviceToken(models.Model):
    """
    Stores mobile device tokens for users.
    These tokens are used to send FCM notifications.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name='User'
    )
    token = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name='FCM Token'
    )
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('android', 'Android'),
            ('ios', 'iOS'),
            ('web', 'Web'),
        ],
        default='android',
        verbose_name='Device Type'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.device_type}"
