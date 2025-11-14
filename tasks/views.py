from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Task, TaskDocument, InvitationCode
from .serializers import (
    UserSerializer, 
    TaskSerializer, 
    TaskDocumentSerializer,
    EmailTokenObtainPairSerializer
)
from .services import send_invitation_email
from django.utils import timezone
import random
import string
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from notifications.models import DeviceToken
from notifications.fcm import send_multicast_notification

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        try:
            # First check if email already exists
            email = request.data.get('email')
            if User.objects.filter(email=email).exists():
                return Response(
                    {'email': ['A user with this email address already exists.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check invitation code
            invitation_code = request.data.get('invitation_code')
            if not invitation_code:
                return Response(
                    {'invitation_code': ['Invitation code is required.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find invitation code
            try:
                invitation = InvitationCode.objects.get(code=invitation_code)
            except InvitationCode.DoesNotExist:
                return Response(
                    {'invitation_code': ['Invalid invitation code.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if code is valid
            if not invitation.is_valid():
                if invitation.is_cancelled:
                    return Response(
                        {'invitation_code': ['This invitation code has been cancelled.']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif invitation.is_used:
                    return Response(
                        {'invitation_code': ['This invitation code has already been used.']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {'invitation_code': ['This invitation code has expired.']},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Does the email address belong to the invited person?
            if invitation.email != email:
                return Response(
                    {'email': ['This email address does not match the invitation code.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create user
            response = super().create(request, *args, **kwargs)

            # If successful, mark invitation code as used
            if response.status_code == 201:
                invitation.is_used = True
                invitation.used_at = timezone.now()
                invitation.save()

            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['GET'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class TaskPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class TaskFilter(filters.FilterSet):
    status = filters.CharFilter(lookup_expr='exact')
    created_at = filters.DateTimeFromToRangeFilter()
    start_date = filters.DateTimeFromToRangeFilter()
    due_date = filters.DateTimeFromToRangeFilter()
    created_by = filters.NumberFilter()
    
    class Meta:
        model = Task
        fields = ['status', 'created_at', 'start_date', 'due_date', 'created_by']

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TaskPagination
    filter_backends = [filters.DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter]
    filterset_class = TaskFilter
    ordering_fields = ['created_at', 'start_date', 'due_date', 'status']
    ordering = ['-created_at']  # Default ordering
    search_fields = ['title']  # Search can be performed in title and description

    def get_queryset(self):
        user = self.request.user
        if user.role == 'site_manager':
            return Task.objects.all()
        return Task.objects.filter(assigned_workers=user)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            # Get current workers before update
            previous_workers = set(instance.assigned_workers.values_list('id', flat=True))
            
            # Get task data
            task_data = request.data
            
            # Update task
            serializer = self.get_serializer(instance, data=task_data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # Process new documents
            starting_documents = []
            if 'starting_documents' in request.FILES:
                starting_documents = request.FILES.getlist('starting_documents', [])
                
                # Save each file in a separate transaction
                for document in starting_documents:
                    try:
                        TaskDocument.objects.create(
                            task=instance,
                            document_type='beginning',
                            file=document,
                            uploaded_by=request.user
                        )
                    except Exception as doc_error:
                        # If error occurs while saving file, log and continue
                        print(f"Error saving update file: {str(doc_error)}")
            
            # Get current task data
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
            
        except Exception as e:
            import traceback
            print(f"Task update error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'An error occurred while updating task: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        try:
            # Get task data
            task_data = request.data.copy()
            
            # Separate files from task_data (to prevent serialization issues)
            starting_documents = []
            if 'starting_documents' in request.FILES:
                starting_documents = request.FILES.getlist('starting_documents', [])
            
            # Create task
            serializer = self.get_serializer(data=task_data)
            serializer.is_valid(raise_exception=True)
            task = serializer.save(created_by=self.request.user)
            
            # Save documents in separate transactions
            for document in starting_documents:
                try:
                    # Save each file in a separate transaction
                    TaskDocument.objects.create(
                        task=task,
                        document_type='beginning',
                        file=document,
                        uploaded_by=self.request.user
                    )
                except Exception as doc_error:
                    # If error occurs while saving file, log and continue
                    print(f"Error saving file: {str(doc_error)}")
            
            # Get current task data
            serializer = self.get_serializer(task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            print(f"Task creation error: {str(e)}")
            print(traceback.format_exc())  # For detailed error information
            return Response(
                {'error': f'Error creating task: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def complete(self, request, pk=None):
        try:
            task = self.get_object()
            
            # Site manager or assigned workers can complete
            if request.user.role != 'site_manager' and request.user not in task.assigned_workers.all():
                return Response(
                    {"detail": "You do not have permission to complete this task."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Separate and process documents
            completion_documents = []
            if 'completion_documents' in request.FILES:
                completion_documents = request.FILES.getlist('completion_documents', [])
            
            # Save each file in a separate transaction
            for document in completion_documents:
                try:
                    TaskDocument.objects.create(
                        task=task,
                        document_type='ending',
                        file=document,
                        uploaded_by=request.user
                    )
                except Exception as doc_error:
                    # If error occurs while saving file, log and continue
                    print(f"Error saving completion file: {str(doc_error)}")

            # Mark task as completed
            task.status = 'completed'
            task.save()

            # Send notification to manager (if the person completing is not the manager)
            if request.user.role != 'site_manager':
                # Get manager's tokens from DeviceToken model
                device_tokens = DeviceToken.objects.filter(
                    user=task.created_by, 
                    is_active=True
                ).values_list('token', flat=True)
                
                if device_tokens:
                    # Send notification
                    notification_data = {
                        'task_id': str(task.id),
                        'task_title': task.title,
                        'task_status': 'completed',
                        'type': 'task_completed',
                        'notification_id': f"task_completed_{task.id}_{request.user.id}"
                    }
                    
                    send_multicast_notification(
                        tokens=list(device_tokens),
                        title="Task Completed",
                        body=f"Task {task.title} has been completed by {request.user.get_full_name()}.",
                        data=notification_data
                    )

            return Response({"detail": "Task completed successfully."})
            
        except Exception as e:
            import traceback
            print(f"Task completion error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": f"An error occurred while completing task: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class DocumentPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class TaskDocumentFilter(filters.FilterSet):
    document_type = filters.CharFilter(lookup_expr='exact')
    uploaded_at = filters.DateTimeFromToRangeFilter()
    task = filters.NumberFilter(field_name='task__id')
    
    class Meta:
        model = TaskDocument
        fields = ['document_type', 'uploaded_at', 'task']

class TaskDocumentViewSet(viewsets.ModelViewSet):
    queryset = TaskDocument.objects.all()
    serializer_class = TaskDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DocumentPagination
    filter_backends = [filters.DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter]
    filterset_class = TaskDocumentFilter
    ordering_fields = ['uploaded_at', 'document_type']
    ordering = ['uploaded_at']
    search_fields = ['file']

    def get_queryset(self):
        user = self.request.user
        task_id = self.kwargs.get('task_pk')
        
        # Site manager can see all documents
        if user.role == 'site_manager':
            if task_id:
                return TaskDocument.objects.filter(task_id=task_id)
            return TaskDocument.objects.all()
        
        # Workers can only see documents of tasks assigned to them
        base_query = TaskDocument.objects.filter(task__assigned_workers=user)
        
        if task_id:
            # If documents of a specific task are requested, must be assigned to that task
            return base_query.filter(task_id=task_id)
        
        return base_query

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

def generate_unique_code(length=6):
    """Generates a unique invitation code"""
    while True:
        # Create code from mixed characters (excluding 0, O, 1, I)
        chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
        code = ''.join(random.choices(chars, k=length))
        
        # Check if code is unique
        if not InvitationCode.objects.filter(code=code).exists():
            return code

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_invitation(request):
    # Only site manager can access
    if request.user.role != 'site_manager':
        return Response({
            'error': 'Only site managers can perform this operation'
        }, status=403)
    
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email address is required'}, status=400)
    
    # Check if email is already registered
    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'This email address already belongs to a registered user'
        }, status=400)
    
    # Active invitation check
    existing_invitation = InvitationCode.objects.filter(
        email=email,
        is_used=False,
        is_cancelled=False,
        expires_at__gt=timezone.now()
    ).first()
    
    if existing_invitation:
        return Response({
            'error': 'An active invitation code already exists for this email'
        }, status=400)
    
    # Create new code
    code = generate_unique_code()
    
    # Save to database
    invitation = InvitationCode.objects.create(
        code=code,
        email=email,
        created_by=request.user,
        expires_at=timezone.now() + timezone.timedelta(hours=24)
    )
    
    # Send email
    try:
        send_invitation_email(email, code)
        return Response({
            'message': 'Invitation code created and email sent',
            'email': email
        }, status=201)
    except Exception as e:
        invitation.delete()
        return Response({
            'error': f'Email could not be sent: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_invitations(request):
    if request.user.role != 'site_manager':
        return Response({
            'error': 'Only site managers can perform this operation'
        }, status=403)
    
    # Get all invitation codes (removed created_by filter)
    invitations = InvitationCode.objects.all().order_by('-created_at')
    
    data = [{
        'id': inv.id,
        'email': inv.email,
        'created_at': inv.created_at,
        'expires_at': inv.expires_at,
        'is_used': inv.is_used,
        'is_expired': inv.expires_at < timezone.now(),
        'is_cancelled': inv.is_cancelled,
        'used_at': inv.used_at,
        'created_by': f"{inv.created_by.first_name} {inv.created_by.last_name}".strip() or inv.created_by.email
    } for inv in invitations]
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_invitation(request, invitation_id):
    # Only site manager can access
    if request.user.role != 'site_manager':
        return Response({
            'error': 'Only site managers can perform this operation'
        }, status=403)
    
    # Find invitation code
    invitation = get_object_or_404(InvitationCode, id=invitation_id)
    
    # Check if code is already used
    if invitation.is_used:
        return Response({
            'error': 'This code has already been used'
        }, status=400)
    
    # Cancel code
    invitation.is_cancelled = True
    invitation.save()
    
    return Response({
        'message': 'Invitation code successfully cancelled'
    })

@api_view(['POST'])
def password_reset_request(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email address is required'}, status=400)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "No user found registered with this email address."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Generate token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = request.get_host()
    reset_link = f"http://{domain}/api/password-reset/{uid}/{token}/"

    # Prepare email content
    context = {
        'user': user,
        'reset_link': reset_link,
    }

    try:
        html_content = render_to_string('password_reset_email.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject='WorkFlow - Password Reset',
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        return Response(
            {"message": "Password reset link has been sent to your email address."},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response({
            'error': f'Email could not be sent: {str(e)}'
        }, status=500)

def password_reset_confirm(request, uidb64, token):
    try:
        # Find user from uid
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Check if token is valid
        if not default_token_generator.check_token(user, token):
            return render(request, 'password_reset_form.html', {
                'error': 'This link is invalid or has expired.'
            })

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                return render(request, 'password_reset_form.html', {
                    'error': 'Passwords do not match!'
                })
            
            # Password security checks
            if len(new_password) < 8:
                return render(request, 'password_reset_form.html', {
                    'error': 'Password must be at least 8 characters long.'
                })
            
            if not any(c.isupper() for c in new_password):
                return render(request, 'password_reset_form.html', {
                    'error': 'Password must contain at least one uppercase letter.'
                })
                
            if not any(c.islower() for c in new_password):
                return render(request, 'password_reset_form.html', {
                    'error': 'Password must contain at least one lowercase letter.'
                })
                
            if not any(c.isdigit() for c in new_password):
                return render(request, 'password_reset_form.html', {
                    'error': 'Password must contain at least one digit.'
                })
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            return render(request, 'password_reset_form.html', {
                'success': 'Your password has been successfully updated! You can log in from the application.'
            })
        
        return render(request, 'password_reset_form.html')
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, 'password_reset_form.html', {
            'error': 'Invalid password reset link.'
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_manual_notification_to_task_workers(request, task_id):
    """
    Sends manual notification to all workers of a specific task for testing purposes.
    URL: /api/manual-notification/task/{task_id}/
    """
    try:
        # Find task
        task = get_object_or_404(Task, id=task_id)
        
        # Check if requester is manager or task owner
        if request.user.role != 'site_manager' and request.user != task.created_by:
            return Response(
                {'error': 'You do not have permission to perform this operation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get workers
        workers = task.assigned_workers.all()
        
        if not workers:
            return Response(
                {'error': 'No worker assigned to this task.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Track sent notifications
        successful_notifications = 0
        failed_notifications = 0
        
        # Send notification to each worker
        for worker in workers:
            # Get tokens from DeviceToken model
            device_tokens = DeviceToken.objects.filter(
                user=worker, 
                is_active=True
            ).values_list('token', flat=True)
            
            if not device_tokens:
                failed_notifications += 1
                continue
            
            # Prepare notification data
            notification_data = {
                'task_id': str(task.id),
                'task_title': task.title,
                'task_status': task.status,
                'type': 'manual_notification',
                'notification_id': f"manual_{task.id}_{worker.id}_{timezone.now().timestamp()}"
            }
            
            # Send notification
            result = send_multicast_notification(
                tokens=list(device_tokens),
                title=f"Task Reminder: {task.title}",
                body=f"A reminder for your task '{task.title}'. Please do not forget to complete your task.",
                data=notification_data
            )
            
            successful_notifications += result['success']
            failed_notifications += result['failure']
        
        return Response({
            'message': f"Notifications sent. Successful: {successful_notifications}, Failed: {failed_notifications}",
            'successful_count': successful_notifications,
            'failed_count': failed_notifications
        })
        
    except Exception as e:
        return Response(
            {'error': f'An error occurred while sending notification: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
