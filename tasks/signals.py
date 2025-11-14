from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Task, User
from notifications.models import DeviceToken
from notifications.fcm import send_multicast_notification
import logging

logger = logging.getLogger(__name__)

@receiver(m2m_changed, sender=Task.assigned_workers.through)
def send_task_assignment_notification(sender, instance, action, pk_set, **kwargs):
    """
    Automatically sends notification when workers are assigned to a task.
    
    This signal is triggered when a Task's assigned_workers ManyToMany relationship changes.
    Notification is sent after workers are added with 'post_add' action.
    """
    # Only work on 'post_add' action (after workers are added)
    if action != 'post_add' or not pk_set:
        return

    try:
        # Get IDs of newly assigned workers
        assigned_worker_ids = list(pk_set)
        
        # Get User objects of assigned workers
        assigned_workers = User.objects.filter(id__in=assigned_worker_ids)
        
        # Prepare necessary data for notification
        task_title = instance.title
        notification_title = "Yeni İş Ataması"
        notification_body = f"'{task_title}' işine atandınız."
        
        # Extra data for notification
        data = {
            "type": "task_assignment",
            "task_id": str(instance.id),
            "task_title": task_title,
            "task_status": instance.status,
            "notification_id": f"task_assignment_{instance.id}_{','.join(map(str, assigned_worker_ids))}"
        }
        
        # Get tokens and send notification separately for each worker
        for worker in assigned_workers:
            # Get worker's active tokens from DeviceToken model
            device_tokens = DeviceToken.objects.filter(
                user=worker, 
                is_active=True
            ).values_list('token', flat=True)
            
            if device_tokens:
                # Send notification
                result = send_multicast_notification(
                    tokens=list(device_tokens),
                    title=notification_title,
                    body=notification_body,
                    data=data
                )
                
                logger.info(
                    f"İş atama bildirimi gönderildi. İşçi: {worker.username}, "
                    f"İş: {instance.title}, Başarılı: {result['success']}, "
                    f"Başarısız: {result['failure']}"
                )
            else:
                logger.warning(f"İşçi {worker.username} için kayıtlı cihaz token'ı bulunamadı.")
    
    except Exception as e:
        logger.error(f"İş atama bildirimi gönderilirken hata oluştu: {e}") 