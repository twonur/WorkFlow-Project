from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Task, TaskDocument

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'phone')
    list_filter = ('role', 'is_staff', 'is_superuser')
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name', 'phone')

    # Fields to display in admin panel
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to display when creating new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'phone'),
        }),
    )

class TaskDocumentInline(admin.TabularInline):
    model = TaskDocument
    extra = 1
    fields = ('document_type', 'file')
    
    def save_model(self, request, obj, form, change):
        obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'due_date', 'status', 'document_count')
    list_filter = ('status', 'created_at', 'due_date')
    search_fields = ('title', 'description')
    filter_horizontal = ('assigned_workers',)
    inlines = [TaskDocumentInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TaskDocument):
                instance.uploaded_by = request.user
            instance.save()
        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def document_count(self, obj):
        starting = obj.documents.filter(document_type='beginning').count()
        ending = obj.documents.filter(document_type='ending').count()
        return format_html(
            '<span style="color: green;">Starting: {}</span><br>'
            '<span style="color: red;">Ending: {}</span>',
            starting, ending
        )
    document_count.short_description = 'Documents'

@admin.register(TaskDocument)
class TaskDocumentAdmin(admin.ModelAdmin):
    list_display = ('task', 'document_type', 'uploaded_by', 'uploaded_at', 'file_preview')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('task__title',)
    readonly_fields = ('uploaded_at',)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        # TaskDocument model's own delete method is called manually
        obj.delete()

    def delete_queryset(self, request, queryset):
        # In bulk delete operations, each document's delete method is called
        for obj in queryset:
            obj.delete()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TaskDocument):
                if not instance.uploaded_by:
                    instance.uploaded_by = request.user
            instance.save()
        formset.save_m2m()

    def file_preview(self, obj):
        if obj.file and obj.file.url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.file.url)
        return format_html('<a href="{}">View File</a>', obj.file.url)
    file_preview.short_description = 'Preview'
