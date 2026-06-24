from django.db import models
from core.models import AbstractModel
from team.models import Team
from django.utils.translation import ugettext_lazy as _

# Create your models here.
class Iteration(AbstractModel): 
    """Iteration status model"""

    """status"""
    STATUS_DO = 'do'
    STATUS_DOING = 'doing'
    STATUS_COMPLETE = 'complete'

    STATUS_CHOICE = (
        (STATUS_DO, 'do'),
        (STATUS_DOING, 'doing'),
        (STATUS_COMPLETE, 'complete')
    )

    name = models.CharField(_('iteration name'), max_length=100, blank=False, help_text=_('Iteration Name'))
    start_date = models.DateField(_('start at'), blank=True, null=True)
    end_date = models.DateField(_('end at'), blank=True, null=True)
    status = models.CharField(_('status'), max_length=16, choices=STATUS_CHOICE, default=STATUS_DO, help_text=_('status'))
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ('-id', )

        