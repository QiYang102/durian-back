import logging
from rich.console import Console

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Tenant, User
from iteration.models import Iteration
from project.models import Project
from story.models import Story
from task.models import Task
import random

from team.models import Team

console = Console()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create Task'

    def __init__(self):
        super().__init__()

    def handle(self, *args, **options):
        logger.info('Create Task - Started')

        all_projects = Project.objects.all()
        all_users = User.objects.all()
        team_instance = Team.objects.get(pk=1)
        tenant = Tenant.objects.first()

        iteration = Iteration.objects.create(
            name='Iteration 11',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timezone.timedelta(days=7)).date(),
            status=Iteration.STATUS_DO,
            team=team_instance,
            tenant=tenant
        )

        for i in range(20):
            story = Story.objects.create(
                description=f'Sample Story {i+1}',
                priority=Story.PRIORITY_NORMAL,
                iteration=iteration,
                project=random.choice(all_projects),
                team=team_instance,
                tenant=tenant
            )

            for j in range(random.randint(1, 10)):
                task = Task.objects.create(
                    description=f'Task {j+1} for Story {i+1}',
                    status=Task.STATUS_DO,
                    story=story,
                    tenant=tenant,
                    user=random.choice(all_users),
                    estimate_time=random.randint(1, 10)
                )

        logger.info('Create Task - Completed')
