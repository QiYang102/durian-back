from rich.console import Console
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from datetime import datetime, timedelta

from story.models import Story
from task.models import Task

console = Console()


class Command(BaseCommand):
    help = 'Migrate story data: update fields and handle old tasks'

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            required=True,
            help='Date in dd-mm-yyyy format (e.g., 09-10-2025)',
        )

    def handle(self, *args, **options):
        date_str = options['date']
        try:
            input_date = datetime.strptime(date_str, '%d-%m-%Y').date()
            
            days_until_sunday = (6 - input_date.weekday()) % 7
            if days_until_sunday == 0 and input_date.weekday() != 6:
                days_until_sunday = 7
            week_ending_date = input_date + timedelta(days=days_until_sunday)
            
            console.print(f'[yellow]Input date: {input_date.strftime("%d-%m-%Y (%A)")}[/yellow]')
            console.print(f'[yellow]Week ending date: {week_ending_date.strftime("%d-%m-%Y (%A)")}[/yellow]')
            console.print(f'[yellow]Migrating stories from iterations ending on or before {week_ending_date.strftime("%d-%m-%Y")}...[/yellow]')
        except ValueError:
            raise CommandError('Date must be in dd-mm-yyyy format (e.g., 09-10-2025)')

        console.print('[yellow]Starting story migration...[/yellow]')

        stories_migrated = 0
        stories_skipped = 0
        stories_failed = 0
        tasks_completed = 0
        tasks_deactivated = 0
        tasks_skipped = 0
        tasks_failed = 0

        with transaction.atomic():
            console.print('[yellow]Getting stories with iterations...[/yellow]')
            
            with console.status('\n[bold green]Fetching stories...'):
                stories_to_migrate = Story.objects.filter(
                    iteration__isnull=False,
                    iteration__end_date__lte=week_ending_date
                )
                total_stories = stories_to_migrate.count()

            if total_stories == 0:
                console.print('[green]No stories found that need migration.[/green]')
                return

            console.print(f'[cyan]Found {total_stories} stories to migrate[/cyan]')

            console.print('[yellow]Updating stories...[/yellow]')
            
            with console.status('\n[bold green]Migrating stories...'):
                stories_to_update = []
                
                for story in stories_to_migrate:
                    try:
                        if story.short_description == story.name and story.status == Story.STATUS_COMPLETED:
                            stories_skipped += 1
                            continue
                        
                        story.short_description = story.name
                        
                        story.is_rnd = False
                        story.need_verify = False
                        story.verify_at = None
                        story.is_multi = False
                        
                        story.status = Story.STATUS_COMPLETED
                        
                        stories_to_update.append(story)
                        stories_migrated += 1
                        
                    except Exception as e:
                        stories_failed += 1
                        continue
                
                if stories_to_update:
                    Story.objects.bulk_update(
                        stories_to_update,
                        ['short_description', 'is_rnd', 'need_verify', 'verify_at', 'is_multi', 'status'],
                        batch_size=1000
                    )

            console.print('[yellow]Handling old tasks...[/yellow]')
            
            with console.status('\n[bold green]Processing tasks...'):
                tasks_to_process = Task.objects.filter(
                    story__iteration__isnull=False,
                    story__iteration__end_date__lte=week_ending_date
                )
                total_tasks = tasks_to_process.count()
                
                console.print(f'[cyan]Found {total_tasks} tasks to process[/cyan]')
                
                tasks_with_user = []
                tasks_without_user = []
                
                for task in tasks_to_process:
                    try:
                        if task.user:
                            if task.status == Task.STATUS_COMPLETE:
                                tasks_skipped += 1
                                continue
                            
                            task.status = Task.STATUS_COMPLETE
                            tasks_with_user.append(task)
                            tasks_completed += 1
                        else:
                            if not task.is_active:
                                tasks_skipped += 1
                                continue
                            
                            task.is_active = False
                            tasks_without_user.append(task)
                            tasks_deactivated += 1
                    except Exception as e:
                        tasks_failed += 1
                        continue
                
                if tasks_with_user:
                    Task.objects.bulk_update(
                        tasks_with_user,
                        ['status'],
                        batch_size=1000
                    )
                
                if tasks_without_user:
                    Task.objects.bulk_update(
                        tasks_without_user,
                        ['is_active'],
                        batch_size=1000
                    )

        console.print('\n[bold cyan]═══ Migration Summary ═══[/bold cyan]')
        console.print(f'[bold cyan]Stories migrated: {stories_migrated}[/bold cyan]')
        console.print(f'[bold cyan]Stories skipped: {stories_skipped}[/bold cyan]')
        console.print(f'[bold cyan]Stories failed: {stories_failed}[/bold cyan]')
        console.print(f'[bold cyan]Tasks completed: {tasks_completed}[/bold cyan]')
        console.print(f'[bold cyan]Tasks deactivated: {tasks_deactivated}[/bold cyan]')
        console.print(f'[bold cyan]Tasks skipped: {tasks_skipped}[/bold cyan]')
        console.print(f'[bold cyan]Tasks failed: {tasks_failed}[/bold cyan]')
        console.print('[green]Story migration completed![/green]')