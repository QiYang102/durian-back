from django.db import models
from core.models import AbstractModel, User
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from iteration.models import Iteration
from story.models import Story
import math
from django.db.models import Sum
from tracking_model import TrackingModelMixin
from model_utils.fields import MonitorField
from decimal import Decimal

# Create your models here.
class Task(AbstractModel, TrackingModelMixin):
    """Task status model"""

    """status"""
    STATUS_DO = 'do'
    STATUS_DOING = 'doing'
    STATUS_COMPLETE = 'complete'
    STATUS_PENDING = 'pending-review'

    STATUS_CHOICE = (
        (STATUS_DO, 'do'),
        (STATUS_DOING, 'doing'),
        (STATUS_COMPLETE, 'complete'),
        (STATUS_PENDING, 'pending-review'),
    )

    description = models.TextField(_('description name'), blank=False, null=False, help_text=_('Description'))
    due_date = models.DateTimeField(_('due at'), blank=True, null=True)
    estimate_time = models.DecimalField(_('estimate time'), blank=True, null=True, decimal_places=2, max_digits=5)
    status = models.CharField(_('status'), max_length=16, choices=STATUS_CHOICE, default=STATUS_DO, help_text=_('status'))
    iteration = models.ForeignKey(to=Iteration, on_delete=models.CASCADE, null=True, blank=True)
    story = models.ForeignKey(to=Story, on_delete=models.CASCADE)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    total_hour_used = models.DecimalField(_('hour'), blank=True, null=True, default=0, decimal_places=2, max_digits=5)
    is_bug = models.BooleanField(_('is bug task'),default=False)
    assigned_at = models.DateTimeField(_('assigned at'), blank=True, null=True)
    status_complete_at = MonitorField(monitor='status', when=[STATUS_COMPLETE], blank=True, null=True, default=None)

    def __str__(self):
        return f'Task #{self.id}'

    def update_total_hour_used(self):
        old_hour_used = self.total_hour_used or 0 
        get_hour_used = self.taskhour_set.filter(is_active=True).aggregate(Sum('hour'))['hour__sum']
        self.total_hour_used = get_hour_used if get_hour_used is not None else 0  # Handle None case

        return not math.isclose(old_hour_used, self.total_hour_used, abs_tol=0.0001)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # If Task is Done, set latest Remaining to 0
        if self.status == Task.STATUS_COMPLETE:
            # Find the latest work log for this task
            latest_log = self.taskhour_set.filter(is_active=True).order_by('-create_at').first()
            
            # Update it only if it's not already 0
            if latest_log and latest_log.remain_hour != 0:
                latest_log.remain_hour = 0
                latest_log.save() 
        
        if self.user and not self.assigned_at:
            now = timezone.now()
            self.assigned_at = now
            self.update_at = now
        else:
            if not self.user:
                self.assigned_at = None

        super().save(force_insert, force_update, using, update_fields)
        # if self.story:
        #     self.story.update_story_status()
        #     self.story.save()

class TaskHour(AbstractModel):
    """Task hour status model"""

    """status"""
    STATUS_FAST = 'fast'
    STATUS_NORMAL = 'normal'
    STATUS_SLOW = 'slow'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICE = (
        (STATUS_FAST, 'fast'),
        (STATUS_NORMAL, 'normal'),
        (STATUS_SLOW, 'slow'),
        (STATUS_CLOSED, 'closed')
    )

    hour = models.DecimalField(_('hour'), blank=True, null=True, default=0, decimal_places=2, max_digits=5)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    task = models.ForeignKey(to=Task, on_delete=models.CASCADE)
    remain_hour = models.DecimalField(_('remain_hour'), blank=True, null=True, default=None, decimal_places=2, max_digits=5)
    status = models.CharField(_('status'), max_length=16, choices=STATUS_CHOICE, default=STATUS_CLOSED)

    def __str__(self):
        return f'TaskHour #{self.task_id} - {self.hour}'

    # update task hour whenever a task hour is updated
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
    # Auto-calculate remain_hour if not explicitly provided
        if self.task and self.task.estimate_time is not None:
            # Treat remain_hour as "not provided" if it's None or 0
            if self.remain_hour is None:
                total_spent = (
                    self.task.taskhour_set
                    .filter(is_active=True)
                    .exclude(id=self.id)
                    .aggregate(total=Sum('hour'))['total'] or Decimal('0')
                )
                self.remain_hour = max(self.task.estimate_time - (total_spent + (self.hour or 0)), 0)

        super().save(force_insert, force_update, using, update_fields)

        # Update task total_hour_used
        if self.task and self.task.update_total_hour_used():
            self.task.save()

class TaskImage(AbstractModel):
    TASK_IMAGE_FOLDER = 'task/image'

    task = models.ForeignKey(to=Task, on_delete=models.CASCADE)
    image = models.ImageField(_('Image'), upload_to=TASK_IMAGE_FOLDER, help_text =_('Image'), blank=True, null=True)


class TaskTemplate(AbstractModel):
    name = models.CharField(_('template name'), max_length=100, blank=False, null=False, help_text=_('Template Name'))

class TaskTemplateItem(AbstractModel):
    task_template = models.ForeignKey(to=TaskTemplate, on_delete=models.CASCADE)
    description = models.TextField(_('description'), blank=False, null=False, help_text=_('Description'))
    estimate_time = models.DecimalField(_('estimate time'), blank=True, null=True, decimal_places=2, max_digits=5)

    ordering = models.PositiveIntegerField(_('ordering'), default=1)