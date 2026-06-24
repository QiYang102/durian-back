from django.apps import AppConfig
from django.db.models.signals import post_save


def base_model_update_hashid(sender, instance, created, **kwargs):
    update_fields = {}

    if (not instance.hashid) and hasattr(instance, 'get_hashid'):
        instance.hashid = instance.get_hashid()
        update_fields['hashid'] = instance.hashid

    if (not instance.name) and instance.AUTO_SEQUENCE_NAME and hasattr(instance, 'get_auto_sequence_name'):
        instance.name = instance.get_auto_sequence_name()
        update_fields['name'] = instance.name

    if len(update_fields):
        sender.objects.filter(pk=instance.pk).update(**update_fields)


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from .base_model import AbstractBaseModel
        from .models import AbstractModel

        for subclass in AbstractBaseModel.__subclasses__():
            post_save.connect(base_model_update_hashid, subclass)

        for subclass in AbstractModel.__subclasses__():
            post_save.connect(base_model_update_hashid, subclass)
