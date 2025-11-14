from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        """
        Runs when application is ready and loads signals.
        """
        import tasks.signals  # Load signals
