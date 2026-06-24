import csv

from ...models import Tenant, User
from ...models import Feature, FeatureAccess

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.db import transaction
from datetime import timedelta

from rich.console import Console

console = Console()


class Command(BaseCommand):
    help = 'Core'

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):

        parser.add_argument(
            '--setup',
            action='store_true',
            help='setup',
        )

    def handle(self, *args, **options):
        if options['setup']:
            self._setup()

        self._feature_handler()

    @transaction.atomic()
    def _setup(self):
        console.print('\n[bold white]Setting up SuperAdmin...')

        tenant, created = Tenant.objects.get_or_create(name='default')
        self._info_created(tenant, created)

        username = settings.LOCAL_ADMIN_USERNAME
        password = settings.LOCAL_ADMIN_PASSWORD

        user, created = User.objects.filter(username=username).get_or_create(email=username, tenant=tenant,
                                                                             defaults=dict(username=username, password=make_password(password), fullname='Super-Admin', is_staff=True, is_superuser=True))
        self._info_created(user, created)

    def _info_created(self, record, created, padding=15):
        model_name = record.__class__.__name__

        if hasattr(record, 'username'):
            record_name = record.username
        elif hasattr(record, 'name'):
            record_name = record.name
        elif hasattr(record, 'title'):
            record_name = record.title
        elif hasattr(record, 'code'):
            record_name = record.code
        else:
            record_name = None

        if not record_name:
            record_name = record.__str__()

        if created:
            console.print(f'  [bold][white]{model_name.ljust(padding)}[/white][/bold] : [cyan]{record_name}[/cyan] [green]created..[/green]')

    def _feature_handler(self):
        ORDERING = 0
        CODE = 1
        NAME = 2

        tenant = Tenant.objects.first()

        with open('core/management/commands/feature-list.csv', mode='r') as csv_file:
            feature_reader = csv.reader(csv_file, delimiter=',')
            next(feature_reader)   # skip header

            console.print('\n[bold white]Updating on Feature...')
            for row in feature_reader:
                ordering = int(row[ORDERING])
                code = row[CODE].strip()
                name = row[NAME].strip()

                self._add_or_update_feature(tenant=tenant, ordering=ordering, code=code, name=name)

    @transaction.atomic()
    def _add_or_update_feature(self, tenant, ordering, code, name):
        feature, created = Feature.objects.get_or_create(code=code, tenant=tenant)

        feature.ordering = ordering
        feature.name = name
        feature.save()

        if created:
            console.print(f'  [bold cyan]{name}[/bold cyan] [green]created..[/green]')
        else:
            console.print(f'  [bold cyan]{name}[/bold cyan] [yellow]updated..[/yellow]')
