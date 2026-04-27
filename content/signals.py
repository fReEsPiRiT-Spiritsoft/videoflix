"""Django signals for automatic video processing.

This module contains signal handlers that automatically trigger video
processing jobs when new videos are uploaded.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from content.models import Video
from content.tasks import process_video
import django_rq


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """Automatically start video processing after upload.
    
    Queues a background job to process the video into HLS format with
    multiple resolutions when a new video is created.
    
    Args:
        sender: Model class (Video).
        instance: Video instance that was saved.
        created: Boolean indicating if this is a new instance.
        **kwargs: Additional signal arguments.
    """
    if created and instance.video_file:
        print(f"New video uploaded: {instance.title}")
        print(f"   -> Starting background processing...")
        
        queue = django_rq.get_queue('default')
        queue.enqueue(process_video, instance.id, job_timeout=3600)