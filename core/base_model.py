import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from sequences import get_next_value

from .utility import hashid_encode


class AbstractBaseModel(models.Model):
    PREFIX = ''
    TIMESTAMP_FORMAT = '%y%m'
    AUTO_SEQUENCE_NAME = False

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    hashid = models.CharField(
        _('hashid'), max_length=16, blank=True, editable=False)

    code = models.CharField(_('code'), max_length=32, blank=True)
    name = models.CharField(_('name'), max_length=255, blank=True)

    is_active = models.BooleanField(_('active'), default=True, help_text=_(
        'Designates whether this record should be treated as active. Unselect this instead of deleting.'))

    create_at = CreationDateTimeField(_('create at'))
    update_at = ModificationDateTimeField(_('update at'))

    class Meta:
        get_latest_by = '-id'
        ordering = ('-id',)
        abstract = True

    def __str__(self):
        return self.name or '-'

    def get_hashid(self):
        return hashid_encode(self.PREFIX, f'{self._meta.app_label}.{self._meta.model_name}', self.pk)

    def get_auto_sequence_name(self):
        tenant_id = self.tenant_id if hasattr(self, 'tenant_id') else 0
        timestamp = self.create_at.strftime(
            self.TIMESTAMP_FORMAT) if self.TIMESTAMP_FORMAT else ''
        sequence_name = f'{self._meta.app_label}.{self._meta.model_name}.{tenant_id}.{timestamp}'.lower()
        sequence = get_next_value(sequence_name)

        return '{0}{1}{2:05d}'.format(self.PREFIX, timestamp, sequence)
