from rest_framework import serializers
from .models import DeviceToken

class DeviceTokenSerializer(serializers.ModelSerializer):
    """
    Serializer for saving and viewing device tokens.
    """
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'device_type', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        """
        If the same token is already registered, updates it.
        Otherwise, creates a new token record.
        """
        user = self.context['request'].user
        token = validated_data.get('token')
        
        # Check if token already exists
        token_obj, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': user,
                'device_type': validated_data.get('device_type', 'android'),
                'is_active': True
            }
        )
        
        return token_obj 