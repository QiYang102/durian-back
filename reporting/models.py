from django.db import models

from team.models import Team


# Create your models here.
class Season(models.Model):
    season_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    report_data = models.JSONField(default=dict)

    class Meta:
        unique_together = ('team', 'start_date')

    def __str__(self):
        return f"Season: {self.start_date} → {self.end_date}"