from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Task, TaskDocument, InvitationCode
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email:
            raise serializers.ValidationError(
                {'email': 'Email address is required.'}
            )
            
        if not password:
            raise serializers.ValidationError(
                {'password': 'Password is required.'}
            )

        # Email format check
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError(
                {'email': 'Please enter a valid email address.'}
            )

        # Find user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'email': 'No user found with this email address.'}
            )

        # Password check
        if not user.check_password(password):
            raise serializers.ValidationError(
                {'password': 'Incorrect password.'}
            )

        # Is user active?
        if not user.is_active:
            raise serializers.ValidationError(
                {'error': 'This account is not active.'}
            )

        # Use email as username
        attrs['username'] = email
        return super().validate(attrs)

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    role = serializers.CharField(source='get_role_display', read_only=True, default='Worker')
    invitation_code = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'phone', 'password', 'invitation_code')
        read_only_fields = ('id',)

    def validate_password(self, value):
        errors = []
        
        if len(value) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if not any(c.isupper() for c in value):
            errors.append('Password must contain at least one uppercase letter.')
            
        if not any(c.islower() for c in value):
            errors.append('Password must contain at least one lowercase letter.')
            
        if not any(c.isdigit() for c in value):
            errors.append('Password must contain at least one digit.')
            
        if errors:
            raise serializers.ValidationError(errors)
            
        return value

    def validate(self, attrs):
        # Check invitation code
        invitation_code = attrs.pop('invitation_code', None)
        email = attrs.get('email')

        if not invitation_code:
            raise serializers.ValidationError({'invitation_code': 'Invitation code is required.'})

        # First check if code is valid
        invitation = InvitationCode.objects.filter(
            code=invitation_code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()

        if not invitation:
            raise serializers.ValidationError({
                'invitation_code': 'Invalid or expired invitation code.'
            })
        
        # Check if email matches
        if invitation.email != email:
            # Mask email (e.g., jo***@example.com)
            masked_email = invitation.email[:3] + '*' * (invitation.email.index('@') - 2) + invitation.email[invitation.email.index('@'):]
            raise serializers.ValidationError({
                'invitation_code': f'This invitation code was created for {masked_email} email address.'
            })

        return attrs

    def create(self, validated_data):
        # Create user
        validated_data['role'] = 'worker'
        validated_data['username'] = validated_data['email']
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Mark invitation code as used
        invitation = InvitationCode.objects.get(
            code=self.initial_data['invitation_code'],
            email=user.email
        )
        invitation.is_used = True
        invitation.used_at = timezone.now()
        invitation.save()

        return user

class TaskDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDocument
        fields = ('id', 'task', 'document_type', 'file', 'uploaded_at', 'uploaded_by')
        read_only_fields = ('id', 'uploaded_at', 'uploaded_by')

class TaskSerializer(serializers.ModelSerializer):
    documents = TaskDocumentSerializer(many=True, read_only=True)
    google_maps_url = serializers.SerializerMethodField()
    assigned_workers_details = UserSerializer(source='assigned_workers', many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'created_at', 'start_date', 'due_date', 
                 'status', 'created_by', 'assigned_workers', 'assigned_workers_details', 'documents',
                 'address', 'latitude', 'longitude', 'google_maps_url')
        read_only_fields = ('id', 'created_at', 'created_by')

    def get_google_maps_url(self, obj):
        return obj.get_google_maps_url()

    def to_representation(self, instance):
        """Customize response"""
        data = super().to_representation(instance)
        # If in list view (multiple tasks are listed)
        if self.context.get('view') and self.context['view'].action == 'list':
            # Return only basic information for each worker
            workers = []
            for worker in instance.assigned_workers.all():
                workers.append({
                    'id': worker.id,
                    'full_name': f"{worker.first_name} {worker.last_name}".strip() or worker.email,
                    'email': worker.email
                })
            data['assigned_workers'] = workers
            # Remove unnecessary detailed data
            data.pop('assigned_workers_details', None)
        else:
            # Show all worker information in detail view
            data['assigned_workers'] = data.pop('assigned_workers_details', [])
        return data 