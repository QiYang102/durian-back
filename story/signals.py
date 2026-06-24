from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from story.models import Story
from task.models import Task

@receiver([post_save, post_delete], sender=Task)
def on_task_post_save(sender, instance, **kwargs):

    if not instance.story:
        return

    story = instance.story if isinstance(instance.story, Story) else Story.objects.get(id=instance.story)
    
    if instance.is_active:
        total = Task.objects.filter(
            story=story,
            is_active=True
        ).aggregate(total=Sum('estimate_time'))['total'] or 0
        
        story.total_estimate_time = total
        story.save(update_fields=['total_estimate_time'])
    
    if story.status not in [Story.STATUS_NEW, Story.STATUS_STARTED, Story.STATUS_TAKEN]:
        return
    
    has_assigned_tasks = Task.objects.filter(
        story=story,
        is_active=True,
        user__isnull=False
    ).exists()
    
    if not has_assigned_tasks and story.status in [Story.STATUS_STARTED, Story.STATUS_TAKEN]:
        story.status = Story.STATUS_NEW
        story.save(update_fields=['status'])