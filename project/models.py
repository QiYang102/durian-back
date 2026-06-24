from django.db import models
from core.models import AbstractModel
from team.models import Team


class Project(AbstractModel):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)

    class Meta:
        ordering = ('name',)
