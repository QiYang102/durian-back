from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from core.models import AbstractModel, User

class AnnouncementQuerySet(models.QuerySet):
    def live(self):
        """Filter announcements that are currently live based on dates"""
        now = timezone.now()
        return self.filter(
            is_active=True,
            is_live=True,
            start_date__lte=now,
            end_date__gte=now
        )
    
class AnnouncementManager(models.Manager):
    def get_queryset(self):
        return AnnouncementQuerySet(self.model, using=self._db)
    
    def live(self):
        return self.get_queryset().live()
    
class Announcement(AbstractModel):
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    start_date = models.DateTimeField(_('Start Date'))
    end_date = models.DateTimeField(_('End Date'))
    description = models.TextField(_('Description'))
    is_live = models.BooleanField(_('Is Live'), default=True)

    objects = AnnouncementManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date']

