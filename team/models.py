from email.policy import default
from django.db import models

from django.utils.translation import ugettext_lazy as _
from core.models import AbstractModel, User


class Team(AbstractModel):
    team_image = models.ImageField(_('Team Image'), upload_to='team_images/', blank=True, null=True, help_text=_('Team Image'))

    class Meta:
            ordering = ['name'] 

    def __str__(self):
        return f'{self.name}'


class TeamMember(AbstractModel):
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)

    class Meta:
            ordering = ['team__name', 'user__fullname']

    def __str__(self):
        return f'{self.team.name} ({self.user.fullname})'
