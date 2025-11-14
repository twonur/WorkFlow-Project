from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'documents', views.TaskDocumentViewSet)

# Nested router: tasks -> documents
tasks_router = NestedSimpleRouter(router, r'tasks', lookup='task')
tasks_router.register(r'documents', views.TaskDocumentViewSet, basename='task-documents')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    path('', include(tasks_router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('token/', views.EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('invitations/create/', views.create_invitation, name='create_invitation'),
    path('invitations/list/', views.list_invitations, name='list_invitations'),
    path('invitations/cancel/<int:invitation_id>/', views.cancel_invitation, name='cancel_invitation'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<str:uidb64>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Notification test endpoint
    path('manual-notification/task/<int:task_id>/', views.send_manual_notification_to_task_workers, name='manual_notification_to_task_workers'),
] 