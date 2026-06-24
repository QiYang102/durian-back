from django.db import models
from core.models import AbstractModel, User
from django.utils.translation import ugettext_lazy as _
from datetime import date


class EventCalendar(AbstractModel):
    """EventCalendar status model"""

    """status"""
    PUBLIC_HOLIDAY = 'Public Holiday'
    ANNUAL_LEAVE = 'Annual Leave'
    ANNUAL_LEAVE_AM = 'Annual Leave AM'
    ANNUAL_LEAVE_PM = 'Annual Leave PM'
    MEDICAL_LEAVE = 'Medical Leave'
    EMERGANCY_LEAVE = 'Emergency Leave'
    EMERGANCY_LEAVE_AM = 'Emergency Leave AM'
    EMERGANCY_LEAVE_PM = 'Emergency Leave PM'
    BIRTHDAY_LEAVE = 'Birthday Leave'
    REPLACEMENT_LEAVE = 'Replacement Leave'
    EVENT = 'Event'
    DEADLINE = 'Deadline'

    EVENT_TYPE = (
        (PUBLIC_HOLIDAY, 'Public Holiday'),
        (ANNUAL_LEAVE, 'Annual Leave'),
        (ANNUAL_LEAVE_AM, 'Annual Leave AM'),
        (ANNUAL_LEAVE_PM, 'Annual Leave PM'),
        (MEDICAL_LEAVE, 'Medical Leave'),
        (EMERGANCY_LEAVE, 'Emergancy Leave'),
        (EMERGANCY_LEAVE_AM, 'Emergancy Leave AM'),
        (EMERGANCY_LEAVE_PM, 'Emergancy Leave PM'),
        (BIRTHDAY_LEAVE, 'Birthday Leave'),
        (REPLACEMENT_LEAVE, 'Replacement Leave'),
        (EVENT, 'Event'),
        (DEADLINE, 'Deadline'),
    )

    start_date = models.DateField(_('start at'), blank=False, null=False)
    end_date = models.DateField(_('end at'), blank=False, null=False)
    type = models.CharField(_('event type'), max_length=18, choices=EVENT_TYPE, default=PUBLIC_HOLIDAY, help_text=_('Event Type'))
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(_('description name'), blank=True, null=True, help_text=_('Description'))
    total_days = models.DecimalField(_('total days'), max_digits=5, decimal_places=2, blank=True, null=True, default=0)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        diff_date = self.end_date - self.start_date
        actual_days = diff_date.days + 1 

        if ('AM' in self.type or 'PM' in self.type):
            self.total_days = actual_days/2
        else:
            self.total_days = actual_days

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        ordering = ('-id',)
