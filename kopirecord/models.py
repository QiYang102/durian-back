from django.db import models
from core.models import AbstractModel, User
from iteration.models import Iteration
from django.utils.translation import ugettext_lazy as _

# Create your models here.

class KopiRecord(AbstractModel):
    """KopiRecord status model"""

    """status"""
    STATUS_OWING = 'owing'
    STATUS_COMPLETE = 'complete'

    STATUS_CHOICE = (
        (STATUS_OWING, 'owing'),
        (STATUS_COMPLETE, 'complete')
    )

    create_date = models.DateField(_('create at'), blank=True, null=True)
    complete_date = models.DateField(_('complete at'), blank=True, null=True)
    iteration = models.ForeignKey(to=Iteration, on_delete=models.CASCADE, null=True, blank=True)
    member_name = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    remark = models.TextField(_('remark'), blank=False, help_text=_('Reason of Owing Kopi'))
    amount = models.PositiveIntegerField(_('kopi amount'), blank=False, null=False, default=1)
    status = models.CharField(_('status'), max_length=16, choices=STATUS_CHOICE, default=STATUS_OWING)

    class Meta:
        ordering = ('-id',)