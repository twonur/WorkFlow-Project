from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('site_manager', 'Site Manager'),
        ('worker', 'Worker'),
    )
    
    email = models.EmailField(_('Email Address'), unique=True)
    role = models.CharField(_('Role'), max_length=15, choices=ROLE_CHOICES)
    phone = models.CharField(_('Phone'), max_length=15)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

class Task(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    start_date = models.DateTimeField(_('Start Date'))
    due_date = models.DateTimeField(_('Due Date'))
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='waiting')
    address = models.CharField(_('Address'), max_length=500, blank=True, null=True)
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    created_by = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='created_tasks',
        verbose_name=_('Created by')
    )
    assigned_workers = models.ManyToManyField(
        'User',
        related_name='assigned_tasks',
        verbose_name=_('Assigned Workers')
    )

    class Meta:
        verbose_name = _('Work')
        verbose_name_plural = _('Work')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_google_maps_url(self):
        """Returns Google Maps URL"""
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        return None

class TaskDocument(models.Model):
    DOCUMENT_TYPES = (
        ('beginning', 'Starting Document'),
        ('ending', 'Ending Document'),
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Work')
    )
    document_type = models.CharField(_('Document Type'), max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(_('File'), upload_to='task_documents/')
    uploaded_at = models.DateTimeField(_('Uploaded At'), auto_now_add=True)
    uploaded_by = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        verbose_name=_('Uploaded By')
    )

    class Meta:
        verbose_name = _('Work Document')
        verbose_name_plural = _('Work Documents')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.task.title} - {self.get_document_type_display()}"

    def delete(self, *args, **kwargs):
        # First delete file from storage
        if self.file:
            self.file.delete(save=False)
        # Then delete database record
        super().delete(*args, **kwargs)

class InvitationCode(models.Model):
    code = models.CharField(max_length=6, unique=True)
    email = models.EmailField()
    created_by = models.ForeignKey('User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.code}"

    def is_valid(self):
        return not self.is_used and not self.is_cancelled and self.expires_at > timezone.now()

    class Meta:
        ordering = ['-created_at'] 