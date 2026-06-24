import csv

from django.contrib import admin
from django.core.files.temp import NamedTemporaryFile
from django.http import HttpResponse

from iteration.models import Iteration
from story.models import Story
from task.models import Task


class ExportIterationAndTaskAction(object):
    def __init__(self, iteration_ids):
        self.iteration_ids = iteration_ids

    def execute(self):
        temporary_file = NamedTemporaryFile(delete=True)
        csv_file = open(temporary_file.name, 'wt', newline='')
        writer = csv.writer(csv_file)

        self.export(writer)

        csv_file.close()
        return temporary_file.name

    def export(self, writer):
        task_queryset = (Task.objects
                         .filter(iteration__id__in=self.iteration_ids)
                         .prefetch_related('story', 'story__project', 'user')
                         .order_by('-iteration__start_date', 'story__project__name', 'story__id', 'id'))

        writer.writerow(['Iteration ID', 'Iteration Name', 'Iteration Start Date', 'Iteration End Date',
                         'Project / Client',
                         'User Story ID', 'User Story Completed',
                         'Task ID', 'Task Owner', 'Task Max', 'Task Effort', 'Task Actual Hour', 'Task Status', 'Task / Bug'])

        for task in task_queryset:
            writer.writerow([task.iteration.id, task.iteration.name, '="' + task.iteration.start_date.strftime('%Y-%m-%d') + '"', '="' + task.iteration.end_date.strftime('%Y-%m-%d') + '"',
                             task.story.project.name if task.story.project else 'Codetinker',
                             task.story.id, 'Y' if task.story.is_complete else 'N',
                             task.id, task.user.username.replace('@codetinker.com', '') if task.user else '-',
                             max(task.estimate_time or 0, task.total_hour_used or 0),
                             task.estimate_time, task.total_hour_used, task.status,
                             'bug' if task.is_bug else 'task'])

    def execute_as_download(self):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="iteration_and_task_export.csv"'

        writer = csv.writer(response)
        self.export(writer)

        return response


@admin.register(Iteration)
class IterationAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'status', 'team')
    list_filter = ('status', 'team',)
    search_fields = ('name', )
    readonly_fields = ()
    autocomplete_fields = ('create_by', 'update_by', 'team')

    actions = ['export_iteration_and_task', 'export_iteration', 'export_user_story',]

    @admin.action(description='Export Iteration and Task')
    def export_iteration_and_task(self, request, queryset):
        iteration_ids = queryset.values_list('id', flat=True)
        export_action = ExportIterationAndTaskAction(iteration_ids)
        return export_action.execute_as_download()

    @admin.action(description='Export Iteration')
    def export_iteration(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="iteration_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Start Date', 'End Date', 'Status'])

        for iteration in queryset:
            writer.writerow([iteration.id, iteration.name, '="' + iteration.start_date.strftime('%Y-%m-%d') + '"', '="' + iteration.end_date.strftime('%Y-%m-%d') + '"', iteration.status])

        return response

    @admin.action(description='Export User Story')
    def export_user_story(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="iteration_userstory_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['Iteration Name', 'User Story ID', 'Project Name', 'Project ID', 'User Story Name', 'User Story Description'])

        user_story_queryset = (Story.objects
                               .filter(iteration__in=queryset)
                               .prefetch_related('project', 'iteration')
                               .order_by('iteration__name', 'id'))

        for story in user_story_queryset:
            writer.writerow([story.iteration.name, story.id, story.project.name if story.project else '-', story.project.id if story.project else '', story.name, story.description])

        return response
