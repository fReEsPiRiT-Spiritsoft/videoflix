from django.db.models.signals import post_save
from django.dispatch import receiver
from content.models import Video
from content.tasks import process_video
import django_rq

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Startet Video-Verarbeitung automatisch nach dem Upload
    """
    if created and instance.video_file:
        # Neues Video → in Queue stellen
        print(f"📹 Neues Video hochgeladen: {instance.title}")
        print(f"   → Starte Verarbeitung in Background...")
        
        queue = django_rq.get_queue('default')
        queue.enqueue(process_video, instance.id, job_timeout=3600)  # 60 Minuten Timeout