import logging
from datetime import date, timedelta
from decimal import Decimal
from rich.console import Console
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

# Import your models
from core.models import Tenant, User
from team.models import Team, TeamMember
from iteration.models import Iteration
from project.models import Project
from story.models import Story
from task.models import Task, TaskHour

console = Console()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates the specific 5-Day Scenario (Task A, B, C) to verify Burndown Math'

    @transaction.atomic
    def handle(self, *args, **options):
        console.print('\n[bold white]🧪 Generating Burndown Test Scenario...[/bold white]')

        # 1. SETUP: Tenant, User, Admin
        tenant, _ = Tenant.objects.get_or_create(name='localhost')
        admin, _ = User.objects.get_or_create(
            username='admin', 
            tenant=tenant, 
            defaults={'email':'admin@test.com', 'fullname':'Admin'}
        )
        
        # 2. SETUP: Team & Project
        team, _ = Team.objects.get_or_create(
            name='Test Team', 
            tenant=tenant, 
            defaults={'create_by':admin, 'update_by':admin}
        )
        
        # --- FIX IS HERE: REMOVED 'role', ADDED 'create_by' ---
        TeamMember.objects.get_or_create(
            team=team, 
            user=admin, 
            tenant=tenant, 
            defaults={
                'create_by': admin,
                'update_by': admin
            }
        )

        project, _ = Project.objects.get_or_create(
            name='Test Project', 
            team=team, 
            tenant=tenant, 
            defaults={'create_by':admin, 'update_by':admin}
        )

        # 3. SETUP: Iteration (Dec 1 to Dec 7)
        start_date = date(2025, 12, 1) # Monday
        end_date = date(2025, 12, 7)   # Sunday
        
        iteration, created = Iteration.objects.get_or_create(
            name='Burndown Verification Sprint',
            tenant=tenant,
            defaults={
                'start_date': start_date,
                'end_date': end_date,
                'status': Iteration.STATUS_DOING,
                'team': team,
                'create_by': admin, 
                'update_by': admin
            }
        )
        
        # If it existed, reset it so we have a clean slate
        if not created:
            console.print("[yellow]Iteration existed. Wiping tasks to restart test...[/yellow]")
            iteration.start_date = start_date
            iteration.end_date = end_date
            iteration.save()
            Task.objects.filter(iteration=iteration).delete()
            Story.objects.filter(iteration=iteration).delete()

        # 4. CREATE STORY
        story = Story.objects.create(
            name="Test Story", 
            iteration=iteration, 
            project=project, 
            team=team, 
            tenant=tenant, 
            create_by=admin,
            update_by=admin, # Added update_by just in case
            status=Story.STATUS_STARTED
        )

        # ==========================================
        # 5. CREATE TASKS (A, B, C)
        # ==========================================
        
        # Task A: 10 Hours (Steady Work)
        task_a = self._create_task(admin, tenant, story, iteration, "Task A (Steady)", 10)
        
        # Task B: 20 Hours (Starts Late - D3)
        task_b = self._create_task(admin, tenant, story, iteration, "Task B (Late)", 20)
        
        # Task C: 8 Hours (Finishes Early - D2)
        task_c = self._create_task(admin, tenant, story, iteration, "Task C (Fast)", 8)

        # ==========================================
        # 6. LOG HISTORY (Backdating logs)
        # ==========================================
        
        # --- DAY 1 (Mon Dec 1) ---
        self._log(task_a, admin, tenant, day_offset=0, hour=2, remain=8, time_str="10:00")
        self._log(task_c, admin, tenant, day_offset=0, hour=4, remain=4, time_str="14:00")

        # --- DAY 2 (Tue Dec 2) ---
        self._log(task_a, admin, tenant, day_offset=1, hour=1, remain=7, time_str="09:00")
        self._log(task_c, admin, tenant, day_offset=1, hour=2, remain=0, status='closed', time_str="11:00")
        
        # --- DAY 3 (Wed Dec 3) ---
        self._log(task_a, admin, tenant, day_offset=2, hour=4, remain=3, time_str="10:00")
        self._log(task_b, admin, tenant, day_offset=2, hour=5, remain=15, time_str="16:00")

        # --- DAY 4 (Thu Dec 4) ---
        self._log(task_b, admin, tenant, day_offset=3, hour=10, remain=5, time_str="13:00")
        
        # --- DAY 5 (Fri Dec 5) ---
        self._log(task_a, admin, tenant, day_offset=4, hour=2, remain=1, time_str="09:00")
        self._log(task_b, admin, tenant, day_offset=4, hour=5, remain=0, status='closed', time_str="15:00")

        console.print(f'\n[bold green]✅ Test Data Created![/bold green]')
        console.print(f'Iteration ID: [cyan]{iteration.id}[/cyan]')
        console.print(f'Start Date: {start_date} | Today (Simulated): Dec 5')

    def _create_task(self, user, tenant, story, iteration, desc, estimate):
        t = Task.objects.create(
            description=desc,
            story=story,
            iteration=iteration,
            estimate_time=Decimal(estimate),
            status=Task.STATUS_DOING,
            user=user,
            tenant=tenant,
            create_by=user,
            update_by=user
        )
        Task.objects.filter(id=t.id).update(create_at=iteration.start_date)
        return t

    def _log(self, task, user, tenant, day_offset, hour, remain, status='normal', time_str="12:00"):
        h, m = map(int, time_str.split(':'))
        log_dt = timezone.datetime(2025, 12, 1) + timedelta(days=day_offset)
        log_dt = log_dt.replace(hour=h, minute=m)
        log_dt = timezone.make_aware(log_dt)

        log = TaskHour.objects.create(
            task=task,
            user=user,
            hour=Decimal(hour),
            remain_hour=Decimal(remain),
            status=status,
            tenant=tenant,
            create_by=user,
            update_by=user
        )
        TaskHour.objects.filter(id=log.id).update(create_at=log_dt)
        console.print(f"Logged: Day {day_offset+1} | {task.description[-8:]} | Rem: {remain}")