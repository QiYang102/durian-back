from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models import Case, CharField, Value, When
from core.models import AbstractModel, User
from iteration.models import Iteration
from project.models import Project
from team.models import Team


# Create your models here.
class Tag(AbstractModel):
    name = models.CharField(_('Tag name'), null=False, blank=False, default="", help_text=_('Tag name'), max_length=255)
    project = models.ForeignKey(to=Project, null=True, blank=True, on_delete=models.CASCADE)
    team = models.ForeignKey(to=Team, null=True,blank=True, on_delete=models.CASCADE)
    color = models.CharField(_('Color'), max_length=7, default="info", help_text=_('Tailwind color e.g. info'))

class Story(AbstractModel): 
    """PRIORITY"""
    PRIORITY_HIGH = 'high'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_LOW = 'low'

    PRIORITY_CHOICE = (
        (PRIORITY_HIGH, 'high'),
        (PRIORITY_NORMAL, 'normal'),
        (PRIORITY_LOW, 'low'),
    )

    """STATUS"""
    STATUS_DRAFT = 'draft'
    STATUS_NEW = 'new'
    STATUS_STARTED = 'started'
    STATUS_TAKEN = 'taken'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICE = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_NEW, 'New'),
        (STATUS_STARTED, 'Started'),
        (STATUS_TAKEN, 'Taken'),
        (STATUS_COMPLETED, 'Completed'),
    )

    """DEPLOYMENT STATUS"""
    DEPLOYMENT_PENDING = 'pending'
    DEPLOYMENT_STAGING = 'staging'
    DEPLOYMENT_PRODUCTION = 'production'

    DEPLOYMENT_STATUS_CHOICE = (
        (DEPLOYMENT_PENDING, 'Pending'),
        (DEPLOYMENT_STAGING, 'Staging'),
        (DEPLOYMENT_PRODUCTION, 'Production'),
    )

    description = models.TextField(_('description name'),null=False , blank=True, default="", help_text=_('Description'))
    is_complete = models.BooleanField(_('is complete'),default=False)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    is_delivered = models.BooleanField(_('is delivered'),default=False)
    is_pendingReview = models.BooleanField(_('is pending review'),default=False)
    is_require_tester = models.BooleanField(_('is is_require_tester'),default=False)
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_CHOICE, default=PRIORITY_NORMAL)
    iteration = models.ForeignKey(to=Iteration, null=True,blank=True, on_delete=models.CASCADE)
    project = models.ForeignKey(to=Project, null=True,blank=True, on_delete=models.CASCADE)
    team=models.ForeignKey(to=Team, null=True,blank=True, on_delete=models.CASCADE)
    parent_story = models.ForeignKey(to='self', null=True,blank=True, on_delete=models.SET_NULL, related_name='+')
    
    is_rnd = models.BooleanField(_('is R&D'), default=False, help_text=_('Indicate if story is R&D'))
    need_verify = models.BooleanField(_('need verify'), default=False, help_text=_('Indicate if story needs verification'))
    verify_at = models.DateTimeField(_('verify at'), null=True, blank=True, help_text=_('Verification timestamp'))
    is_multi = models.BooleanField(_('is multiple'), default=False, help_text=_('Indicate if this story should be done by multiple user'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICE, default=STATUS_DRAFT, help_text=_('Current status of the story'))
    short_description = models.CharField(_('short description'), max_length=255, blank=True, null=True, help_text=_('Short description of user story'))
    total_estimate_time = models.DecimalField(_('total estimate time'), blank=True, null=True, default=0, decimal_places=2, max_digits=5, help_text=_('Total estimated time in hours'))

    is_needed_to_deploy = models.BooleanField(_('is needed to deploy'), default=False, help_text=_('Indicate if this story requires deployment'))
    deployment_status = models.CharField(_('deployment status'), max_length=20, choices=DEPLOYMENT_STATUS_CHOICE, default=DEPLOYMENT_PENDING, help_text=_('Current deployment status'))
    deployment_staging_status_at = models.DateTimeField(_('deployed to staging at'), null=True, blank=True, help_text=_('Timestamp when deployed to staging'))
    deployment_production_status_at = models.DateTimeField(_('deployed to production at'), null=True, blank=True, help_text=_('Timestamp when deployed to production'))
    has_issue = models.BooleanField(_('has issue'), default=False, help_text=_('Indicate if this story has deployment or post-deployment issues'))
    issue_resolved_at = models.DateTimeField(_('issue resolved at'), null=True, blank=True, help_text=_('Timestamp when issue was resolved'))

    tags = models.ManyToManyField(to='Tag', through='TagItem',related_name='stories',blank=True)

    class Meta:
        # order by priority first, then for story in same priority, order by -id
        ordering = [
            Case(
                When(priority='low', then=Value(2)),
                When(priority='normal', then=Value(1)),
                When(priority='high', then=Value(0)),
                default=Value(1),
                output_field=CharField(),
            ),
            '-id']
        verbose_name_plural = 'User Stories'

    def __str__(self):
        return f'Story #{self.id}'
    
    def save(self, *args, **kwargs):
        if self.status == Story.STATUS_COMPLETED :
            if not self.completed_at:
                self.completed_at = timezone.now()
        else:
            self.completed_at = None
        
        super().save( *args, **kwargs)
        
        
class StoryImage(AbstractModel):
    STORY_IMAGE_FOLDER = 'story/image'

    story = models.ForeignKey(to=Story, on_delete=models.CASCADE)
    image = models.ImageField(_('Image'), upload_to=STORY_IMAGE_FOLDER, help_text =_('Image'), blank=True, null=True)   

class VerifiedByUser(AbstractModel):    
    story = models.ForeignKey(to=Story, on_delete=models.CASCADE)
    iteration = models.ForeignKey(to=Iteration, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    total_hour_used = models.DecimalField(_('total hour used'), blank=True, null=True, default=0, decimal_places=2, max_digits=5)
    
    def __str__(self):
        return f'StoryVerification #{self.story_id} by {self.user}'

class TagItem(models.Model):
    tag = models.ForeignKey(to=Tag, null=True, blank=True, on_delete=models.CASCADE)
    story = models.ForeignKey(to=Story, null=True, blank=True, on_delete=models.CASCADE)