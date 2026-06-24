import logging
from rich.console import Console
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from core.models import Tenant, User
from team.models import Team, TeamMember
from iteration.models import Iteration
from project.models import Project
from story.models import Story
from task.models import Task, TaskHour
import random
from decimal import Decimal
from datetime import timedelta

console = Console()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create comprehensive dummy data for teams, iterations, stories, tasks, and task hours'

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing data before creating new dummy data',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        logger.info('Create Dummy Data - Started')
        console.print('\n[bold white]Creating comprehensive dummy data...')

        if options['clean']:
            self._clean_existing_data()

        # Get or create tenant and users
        tenant = self._get_or_create_tenant()
        users = self._get_or_create_users(tenant)

        # Create teams
        teams = self._create_teams(tenant, users)
        
        # Create projects for teams
        projects = self._create_projects(teams, tenant, users)
        
        # Create iterations for each team
        iterations = self._create_iterations(teams, tenant, users)
        
        # Create stories and tasks
        self._create_stories_and_tasks(iterations, projects, users, tenant)

        console.print('\n[bold green]Dummy data creation completed successfully!')
        logger.info('Create Dummy Data - Completed')

    def _clean_existing_data(self):
        console.print('[yellow]Cleaning existing dummy data...')
        # Clean based on team names
        TaskHour.objects.filter(task__story__team__name__in=['Tech Team', 'Intern Team']).delete()
        Task.objects.filter(story__team__name__in=['Tech Team', 'Intern Team']).delete()
        Story.objects.filter(team__name__in=['Tech Team', 'Intern Team']).delete()
        Iteration.objects.filter(team__name__in=['Tech Team', 'Intern Team']).delete()
        # Clean projects
        Project.objects.filter(team__name__in=['Tech Team', 'Intern Team']).delete()
        # Clean team members first, then teams
        TeamMember.objects.filter(team__name__in=['Tech Team', 'Intern Team']).delete()
        Team.objects.filter(name__in=['Tech Team', 'Intern Team']).delete()
        console.print('[green]Existing dummy data cleaned.')
    
    def _get_or_create_tenant(self):
        tenant, created = Tenant.objects.get_or_create(
            name='localhost',
            defaults={'name': 'localhost'}
        )
        if created:
            console.print(f'[green]Created tenant: {tenant.name}')
        return tenant

    def _get_or_create_users(self, tenant):
        users = list(User.objects.filter(tenant=tenant)[:10])
        
        if len(users) < 5:
            console.print('[yellow]Creating additional users for dummy data...')
            user_data = [
                ('john_doe', 'John Doe', 'john@example.com'),
                ('jane_smith', 'Jane Smith', 'jane@example.com'),
                ('bob_wilson', 'Bob Wilson', 'bob@example.com'),
                ('alice_brown', 'Alice Brown', 'alice@example.com'),
                ('charlie_davis', 'Charlie Davis', 'charlie@example.com'),
            ]
            
            for username, fullname, email in user_data:
                user, created = User.objects.get_or_create(
                    username=username,
                    tenant=tenant,
                    defaults={
                        'fullname': fullname,
                        'email': email,
                        'capacity': random.randint(6, 8),
                        'role': User.ROLE_MEMBER,
                    }
                )
                if created:
                    users.append(user)
                    console.print(f'[green]Created user: {fullname}')

        return users[:10] if len(users) >= 10 else users

    def _create_projects(self, teams, tenant, users):
        projects = []
        admin_user = users[0] if users else None
        
        # Create 2-3 projects per team
        project_templates = [
            'E-Commerce Platform',
            'Customer Portal',
            'Admin Dashboard',
            'Mobile App API',
            'Analytics System',
            'Payment Gateway Integration'
        ]
        
        for team in teams:
            num_projects = random.randint(2, 3)
            
            # Choose different project names for each team
            available_projects = project_templates.copy()
            random.shuffle(available_projects)
            
            for i in range(num_projects):
                project_name = available_projects[i % len(available_projects)]
                
                project = Project.objects.create(
                    name=f'{project_name} - {team.name}',
                    team=team,
                    tenant=tenant,
                    create_by=admin_user,
                    update_by=admin_user,
                )
                
                projects.append(project)
                console.print(f'[green]Created project: {project.name}')
        
        return projects

    def _create_teams(self, tenant, users):
        teams = []
        team_data = [
            ('Tech Team', 'Senior developers and technical leads'),
            ('Intern Team', 'Junior developers and interns'),
        ]

        admin_user = users[0] if users else None

        for name, description in team_data:
            team = Team.objects.create(
                name=name,
                tenant=tenant,
                create_by=admin_user,
                update_by=admin_user,
            )
            
            # Tech team gets more experienced members (4-6), Intern team gets fewer (3-4)
            if 'Tech' in name:
                team_size = random.randint(4, min(6, len(users)))
            else:
                team_size = random.randint(3, min(4, len(users)))
            
            team_users = random.sample(users, team_size)
            for user in team_users:
                TeamMember.objects.create(
                    team=team,
                    user=user,
                    tenant=tenant,
                    create_by=admin_user,
                    update_by=admin_user,
                )
            
            teams.append(team)
            console.print(f'[green]Created team: {name} with {len(team_users)} members')

        return teams

    def _create_iterations(self, teams, tenant, users):
        iterations = []
        
        admin_user = users[0] if users else None
        
        # Get current date for realistic iteration naming
        current_date = timezone.now().date()
        
        # Calculate week number
        def get_week_identifier(date):
            # Get ISO week number and format as YYYY-MM-WX
            year = date.year
            month = date.month
            # Calculate which week of the month this is
            first_day_of_month = date.replace(day=1)
            days_into_month = (date - first_day_of_month).days
            week_of_month = (days_into_month // 7) + 1
            return f"{year}-{month:02d}-W{week_of_month}"

        for team in teams:
            for iter_idx in range(3):  # 3 iterations per team
                # Create iterations spanning different weeks
                start_date = current_date + timedelta(days=iter_idx * 14 - 21)  # Start 3 weeks ago
                end_date = start_date + timedelta(days=13)  # 2-week sprints
                
                iteration_name = get_week_identifier(start_date)
                
                # Vary iteration status based on dates realistically
                if start_date > current_date:
                    status = Iteration.STATUS_DO
                elif end_date < current_date:
                    status = Iteration.STATUS_COMPLETE
                else:
                    status = random.choice([Iteration.STATUS_DOING, Iteration.STATUS_COMPLETE])

                iteration = Iteration.objects.create(
                    name=iteration_name,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    team=team,
                    tenant=tenant,
                    create_by=admin_user,
                    update_by=admin_user,
                )
                
                iterations.append(iteration)
                console.print(f'[green]Created iteration: {iteration.name} for {team.name} ({status})')

        return iterations

    def _create_stories_and_tasks(self, iterations, projects, users, tenant):
        tech_team_stories = {
            "User authentication system": "Implement JWT-based authentication with refresh tokens and secure password hashing",
            "API rate limiting implementation": "Add middleware to limit requests per minute per user to prevent abuse",
            "Database backup automation": "Configure nightly PostgreSQL backups with retention policy and S3 upload",
            "CI/CD pipeline setup": "Set up GitHub Actions pipeline with automated tests and staging deployment",
            "System monitoring dashboard": "Integrate Prometheus and Grafana dashboards for live metrics",
            "OAuth2 integration": "Enable Google and GitHub login using OAuth2 provider",
            "Performance optimization": "Profile bottlenecks and apply caching, query optimization, and indexing",
            "Security vulnerability patches": "Upgrade dependencies and apply patches for known CVEs",
            "Microservices architecture": "Refactor monolith into microservices with Docker and Kubernetes",
            "Automated testing framework": "Introduce pytest-based testing framework with coverage reports"
        }

        intern_team_stories = {
            "Loading indicators implementation": "Add animated loading spinners for async data fetches",
            "Form validation system": "Implement client-side and server-side validation with clear error messages",
            "Table sorting functionality": "Enable ascending/descending sorting on table columns",
            "Mobile responsive layout": "Adapt components to mobile devices using flexbox and media queries",
            "CSV export feature": "Allow users to export filtered table data into CSV format",
            "Breadcrumb navigation": "Implement breadcrumb navigation for better user flow",
            "Search with filters": "Add search bar with filter options and debounce support",
            "Pagination component": "Build reusable pagination component with page size options",
            "Tooltip system": "Add tooltips to buttons and icons for better UX",
            "Confirmation dialogs": "Show confirmation dialogs before destructive actions"
        }

        tech_tasks = [
            "Set up database schema and migrations",
            "Implement authentication middleware",
            "Create unit tests with 80% coverage",
            "Set up Redis caching layer",
            "Configure Docker containers",
            "Implement error handling and logging",
            "Set up monitoring with Prometheus",
            "Code review and refactoring",
            "Security vulnerability assessment",
            "Performance optimization and profiling",
            "API documentation with Swagger",
            "Database query optimization"
        ]
        
        intern_tasks = [
            "Create responsive CSS layouts",
            "Implement form validation logic",
            "Write frontend component tests",
            "Update user interface designs",
            "Fix minor UI bugs and styling issues",
            "Create loading spinners and animations",
            "Implement basic CRUD operations",
            "Update documentation and comments",
            "Test user flows manually",
            "Create mockups and wireframes"
        ]

        priorities = [Story.PRIORITY_HIGH, Story.PRIORITY_NORMAL, Story.PRIORITY_LOW]
        task_statuses = [Task.STATUS_DO, Task.STATUS_DOING, Task.STATUS_COMPLETE, Task.STATUS_PENDING]
        story_statuses = [Story.STATUS_NEW, Story.STATUS_STARTED, Story.STATUS_TAKEN, Story.STATUS_COMPLETED]
        
        admin_user = users[0] if users else None

        for iteration in iterations:
            # Choose appropriate stories based on team type
            if 'Tech' in iteration.team.name:
                story_pool = tech_team_stories.copy()
                task_pool = tech_tasks
                priority_weights = [0.3, 0.5, 0.2]  # 30% high, 50% normal, 20% low
            else:
                story_pool = intern_team_stories.copy()
                task_pool = intern_tasks
                priority_weights = [0.1, 0.6, 0.3]  # 10% high, 60% normal, 30% low
            
            # Shuffle stories for variety
            story_titles = list(story_pool.keys())
            random.shuffle(story_titles)
            
            # Create 10 stories per iteration
            for story_idx in range(10):
                story_title = story_titles[story_idx % len(story_titles)]
                story_desc = story_pool[story_title]

                # Weight the priority selection
                priority = random.choices(priorities, weights=priority_weights)[0]
                
                # Select project from the same team
                team_projects = [p for p in projects if p.team == iteration.team]
                selected_project = random.choice(team_projects) if team_projects else None
                
                # Generate story name with iteration reference
                story_name = story_title
                short_desc = story_desc
                
                # Determine story characteristics
                is_rnd = random.random() < 0.1  # 10% R&D stories
                is_multi = random.random() < 0.2  # 20% multi stories
                need_verify = random.random() < 0.3 if 'Tech' in iteration.team.name else random.random() < 0.15
                
                # Status distribution based on iteration status
                if iteration.status == Iteration.STATUS_COMPLETE:
                    status = random.choice([Story.STATUS_COMPLETED, Story.STATUS_COMPLETED, Story.STATUS_TAKEN])
                elif iteration.status == Iteration.STATUS_DOING:
                    status = random.choice([Story.STATUS_STARTED, Story.STATUS_TAKEN, Story.STATUS_NEW])
                else:
                    status = Story.STATUS_NEW
                
                story = Story.objects.create(
                    name=story_name,
                    description=short_desc,
                    short_description=short_desc,
                    priority=priority,
                    iteration=iteration,
                    project=selected_project,
                    team=iteration.team,
                    tenant=tenant,
                    create_by=admin_user,
                    update_by=admin_user,
                    is_require_tester=random.choice([True, False]) if 'Tech' in iteration.team.name else random.choice([False, False, True]),
                    is_rnd=is_rnd,
                    is_multi=is_multi,
                    need_verify=need_verify,
                    status=status,
                )

                # Create 1-2 tasks per story
                num_tasks = random.randint(1, 2)
                task_estimates = []

                for task_idx in range(num_tasks):
                    task_desc = random.choice(task_pool)
                    
                    # Assign task to a team member
                    team_members = list(iteration.team.teammember_set.all())
                    assigned_user = random.choice(team_members).user if team_members else random.choice(users)

                    # Tech team gets longer estimates, intern team gets shorter
                    # Use 0.5 increments for readability (0.5, 1.0, 1.5, 2.0, etc.)
                    if 'Tech' in iteration.team.name:
                        estimate_hours = random.choice([2.0, 2.5, 3.0, 4.0, 4.5, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0])
                        bug_chance = 0.15  # 15% chance of bug tasks
                    else:
                        estimate_hours = random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0])
                        bug_chance = 0.05  # 5% chance of bug tasks

                    task = Task.objects.create(
                        description=task_desc,
                        status=random.choice(task_statuses),
                        story=story,
                        iteration=iteration,
                        user=assigned_user,
                        tenant=tenant,
                        create_by=admin_user,
                        update_by=admin_user,
                        estimate_time=Decimal(str(estimate_hours)),
                        is_bug=random.random() < bug_chance,
                    )

                    task_estimates.append(Decimal(str(estimate_hours)))

                    # Create task hours for completed or in-progress tasks
                    if task.status in [Task.STATUS_COMPLETE, Task.STATUS_DOING, Task.STATUS_PENDING]:
                        self._create_task_hours(task, assigned_user, tenant, admin_user)

                story.total_estimate_time = sum(task_estimates)
                story.save(update_fields=["total_estimate_time"])

            console.print(f'[green]Created 10 realistic stories with tasks for {iteration.team.name} - {iteration.name}')

    def _create_task_hours(self, task, assigned_user, tenant, admin_user):
        # Create realistic task hour entries
        num_entries = random.randint(1, 4)  # 1-4 work sessions
        total_hours = 0
        
        task_hour_statuses = [TaskHour.STATUS_NORMAL, TaskHour.STATUS_FAST, TaskHour.STATUS_SLOW, TaskHour.STATUS_CLOSED]
        status_weights = [0.6, 0.2, 0.15, 0.05]  # Most work is normal pace
        
        for entry_idx in range(num_entries):
            # Realistic work session lengths - 0.5 increments (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
            hours_worked = Decimal(str(random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])))
            total_hours += float(hours_worked)
            
            # Calculate remaining hours realistically
            if task.estimate_time:
                remain_hours = max(0, float(task.estimate_time) - total_hours)
                # Add some variance - sometimes developers underestimate
                if remain_hours == 0 and random.random() < 0.3:
                    remain_hours = random.choice([0.5, 1.0, 1.5, 2.0])
            else:
                remain_hours = random.choice([0, 0.5, 1.0, 1.5, 2.0, 3.0])
            
            status = random.choices(task_hour_statuses, weights=status_weights)[0]
            
            TaskHour.objects.create(
                hour=hours_worked,
                user=assigned_user,
                task=task,
                remain_hour=Decimal(str(remain_hours)),
                status=status,
                tenant=tenant,
                create_by=admin_user,
                update_by=admin_user,
            )