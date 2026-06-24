from django.db.models.signals import post_save
from django.dispatch import receiver
from task.models import Task, TaskImage, TaskHour
from core import utility

TO_UPDATE_WHEN_TASK_DELETED = ['is_active']

@receiver(post_save, sender=Task)
def remove_taskHour_and_taskImage(sender, instance, created, **kwargs):
    
    need_remove_task = utility.has_key_in_list(instance.tracker.changed, TO_UPDATE_WHEN_TASK_DELETED)
    if need_remove_task and instance.is_active==False:
        
        related_taskImage = TaskImage.objects.filter(task=instance).filter(is_active=True)

        related_taskHour = TaskHour.objects.filter(task=instance).filter(is_active=True)

        if related_taskImage.exists():
            related_taskImage.update(is_active=False)

        if related_taskHour.exists():
            related_taskHour.update(is_active=False)

@receiver(post_save, sender=TaskHour)
def determine_status(sender, instance, created, **kwargs):
    if created:
        task_object = Task.objects.get(pk=instance.task.pk)
        estimate_time = task_object.estimate_time
        total_hour_used = task_object.total_hour_used
        used_hours = instance.hour
        remain_hour = instance.remain_hour
        total_estimate_time_to_used = total_hour_used + used_hours + remain_hour
        task_hour_object = TaskHour.objects.get(pk=instance.pk)
        if(remain_hour == 0):
            task_hour_object.status='closed'
        elif(total_estimate_time_to_used < estimate_time):
            task_hour_object.status='fast'
        elif(total_estimate_time_to_used == estimate_time):
            task_hour_object.status='normal'
        elif(total_estimate_time_to_used > estimate_time):
            task_hour_object.status='slow'
        task_hour_object.save()