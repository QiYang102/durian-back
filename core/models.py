from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser

from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField

from .base_model import AbstractBaseModel

class Tenant(AbstractBaseModel):
    PREFIX = 'T'


class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class User(AbstractUser, TenantAwareModel):
    """User model"""

    """Role"""
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'

    ROLE_CHOICE = (
        (ROLE_ADMIN, 'admin'),
        (ROLE_MEMBER, 'member'),
    )

    USER_IMAGE_FOLDER = 'user/image'

    image = models.ImageField(_('Image'), upload_to=USER_IMAGE_FOLDER, help_text =_('Image'), blank=True, null=True)
    fullname = models.CharField(_('fullname'), max_length=100)
    capacity = models.PositiveIntegerField(_('capacity'), default=0)

    # mobile_prefix and msisdn is not in used
    mobile_prefix = models.CharField(_('mobile prefix'), max_length=6, blank=True, default='6012')
    msisdn = models.CharField(_('msisdn'), max_length=20, blank=True, help_text=_('Mobile Station Integrated Services Digital Network'))

    mobile_number = models.CharField(_('mobile number'), max_length=20, blank=True)

    device_token = models.CharField(_('device token'), max_length=255, blank=True)

    is_verify = models.BooleanField(_('is verified'), default=False)
    role = models.CharField(_('role'), max_length=16, choices=ROLE_CHOICE, default=ROLE_ADMIN)

    create_by = models.ForeignKey('self', blank=True, null=True, related_name='+', on_delete=models.SET_NULL)
    update_by = models.ForeignKey('self', blank=True, null=True, related_name='+', on_delete=models.SET_NULL)

    update_at = ModificationDateTimeField(_('update at'))

    @property
    def is_customer(self):
        return self.role == User.ROLE_TYPE

    @property
    def has_user_access(self):
        return self.featureaccess_set.filter(feature__code='user').exists()

    @staticmethod
    def is_valid_role(role):
        return role in map(lambda x: x[0], User.ROLE_CHOICE)

    # def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
    #     self.mobile_number = self.mobile_number.replace(
    #         ' ', '').replace('-', '') if self.mobile_number else ''
    #     self.msisdn = f'{self.mobile_prefix}{self.mobile_number}'.replace(
    #         '+', '') if self.mobile_number else ''

    #     super().save(force_insert, force_update, using, update_fields)
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.mobile_number = self.mobile_number.replace(' ', '').replace('-', '') if self.mobile_number else ''
        
        if self.mobile_number and not self.msisdn:
            self.msisdn = f'{self.mobile_prefix}{self.mobile_number}'.replace('+', '')
        
        super().save(force_insert, force_update, using, update_fields)


class UserAwareModel(models.Model):
    create_by = models.ForeignKey(
        User, null=True, blank=False, related_name='+', on_delete=models.CASCADE)
    update_by = models.ForeignKey(
        User, null=True, blank=False, related_name='+', on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Feature(TenantAwareModel):
    """
    Represents the feature
    """
    code = models.CharField(_('code'), max_length=32)
    name = models.CharField(_('name'), max_length=255)

    ordering = models.PositiveSmallIntegerField(_('ordering'), default=0)
    is_active = models.BooleanField(_('active'), default=True)

    create_at = CreationDateTimeField(_('create at'))

    class Meta:
        verbose_name = _('feature')
        verbose_name_plural = _('features')
        ordering = ['ordering', 'code', 'id']

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{0}-{1} {2}'.format(self.__class__.__name__, self.code, self.name)


class FeatureAccess(TenantAwareModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)

    create_at = CreationDateTimeField(_('create at'))

    class Meta:
        verbose_name = _('feature access')
        verbose_name_plural = _('features access')
        ordering = ['id']

    def __str__(self):
        return '{0} - {1}'.format(self.id, self.feature)

    def __repr__(self):
        return '{0}-{1} {2}'.format(self.__class__.__name__, self.id, self.feature)


class ActiveAbstractModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class AbstractModel(AbstractBaseModel, TenantAwareModel, UserAwareModel):
    class Meta:
        abstract = True

    objects = models.Manager()
    db_objects = models.Manager()


# class Test(AbstractModel):
#     pass
