from django.apps import AppConfig
from django.db.models.signals import post_migrate

class MealTogetherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meal_together'

    def ready(self):
        
        
        from django.dispatch import receiver       

        @receiver(post_migrate)
        def schedule_tasks(sender, **kwargs):
            from meal_together.tasks import send_deadline_notifications
            send_deadline_notifications(repeat=60)
