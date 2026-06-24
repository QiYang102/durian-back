import os
from wsgiref.util import FileWrapper

from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django import forms
from django.utils import timezone


from core.excel import ExcelExport
from core.utility import tenant_from_request
from story import story_service
from story.models import Tag, Story, StoryImage, VerifiedByUser, TagItem
from project.models import Project


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']
    search_fields = ['name']

@admin.register(TagItem)
class TagItemAdmin(admin.ModelAdmin):
    list_display = ['tag', 'story']

class TagItemInline(admin.TabularInline):
    model = TagItem
    extra = 1
    autocomplete_fields = ['tag']

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'description', 'is_complete', 'parent_story', 'priority', 'iteration', 'team',  'is_delivered', 'status', 'is_multi', 'is_rnd',
                    'is_needed_to_deploy', 'deployment_status', 'has_issue')
    list_filter = ('team', 'priority', 'project', 'iteration', 'status', 'is_multi', 'is_rnd', 'need_verify', 'is_complete',
                   'is_needed_to_deploy', 'deployment_status', 'has_issue')
    search_fields = ('name', 'description', 'parent_story__name', 'short_description')
    readonly_fields = ('is_complete', 'verify_at')
    inlines = [TagItemInline]
    actions = ['to_stickyme_basecamp',
               'to_codetinker_react', 'to_codetinker_knowledge', 'to_codetinker_chase',
               'to_codetinker_web', 'to_codetinker_roundtable',
               'to_sunway_pms', 'to_sunway_obs']
    autocomplete_fields = ['create_by', 'update_by', 'iteration', 'project', 'team', 'parent_story']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('iteration', 'project', 'team', 'parent_story')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv), path('download_template/', self.download_template_file)]
        return new_urls + urls

    def upload_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            # option_reader = csv.reader(codecs.iterdecode(csv_file, 'utf-8'), delimiter=',')
            tenant = tenant_from_request(request)

            model_created_count = story_service.import_story_csv_file(csv_file, tenant)

            result = dict(model_created=model_created_count)
            messages.success(request, 'Upload completed (%s)' % result)

            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/story_upload.html", data)

    def download_template_file(self, request):
        export = ExcelExport()

        template_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'import_story_csv_sample.csv')

        file = open(template_file, 'rb')
        download_filename = '{0}.csv'.format('import_story_csv_sample')

        response = HttpResponse(FileWrapper(file), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = export.rfc5987_content_disposition(download_filename)

        return response

    @admin.action(description='Mark as "StickyMe:BaseCamp"')
    def to_stickyme_basecamp(self, request, queryset):
        project = Project.objects.get(name='StickyMe:BaseCamp')
        queryset.update(project=project)

    @admin.action(description='Mark as "Codetinker:Chase"')
    def to_codetinker_chase(self, request, queryset):
        project = Project.objects.get(name='Codetinker:Chase')
        queryset.update(project=project)

    @admin.action(description='Mark as "Codetinker:Knowledge"')
    def to_codetinker_knowledge(self, request, queryset):
        project = Project.objects.get(name='Codetinker:Knowledge')
        queryset.update(project=project)

    @admin.action(description='Mark as "Codetinker:React"')
    def to_codetinker_react(self, request, queryset):
        project = Project.objects.get(name='Codetinker:React')
        queryset.update(project=project)

    @admin.action(description='Mark as "Codetinker:RoundTable"')
    def to_codetinker_roundtable(self, request, queryset):
        project = Project.objects.get(name='Codetinker:RoundTable')
        queryset.update(project=project)

    @admin.action(description='Mark as "Codetinker:Web"')
    def to_codetinker_web(self, request, queryset):
        project = Project.objects.get(name='Codetinker:Web')
        queryset.update(project=project)

    @admin.action(description='Mark as "Sunway:PMS"')
    def to_sunway_pms(self, request, queryset):
        project = Project.objects.get(name='Sunway:PMS')
        queryset.update(project=project)

    @admin.action(description='Mark as "Sunway:OBS"')
    def to_sunway_obs(self, request, queryset):
        project = Project.objects.get(name='Sunway:OBS')
        queryset.update(project=project)

    @admin.action(description='Mark as "Needs Deployment"')
    def mark_needs_deployment(self, request, queryset):
        queryset.update(is_needed_to_deploy=True)
        self.message_user(request, f'{queryset.count()} stories marked as needing deployment.')

    @admin.action(description='Mark as "Deployed to Staging"')
    def mark_deployed_to_staging(self, request, queryset):
        queryset.update(
            deployment_status=Story.DEPLOYMENT_STAGING,
            deployment_staging_status_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} stories marked as deployed to staging.')

    @admin.action(description='Mark as "Deployed to Production"')
    def mark_deployed_to_production(self, request, queryset):
        queryset.update(
            deployment_status=Story.DEPLOYMENT_PRODUCTION,
            deployment_production_status_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} stories marked as deployed to production.')

    @admin.action(description='Mark as "Has Issue"')
    def mark_has_issue(self, request, queryset):
        queryset.update(has_issue=True)
        self.message_user(request, f'{queryset.count()} stories marked as having issues.')

    @admin.action(description='Mark as "Issue Resolved"')
    def mark_issue_resolved(self, request, queryset):
        queryset.update(
            has_issue=False,
            issue_resolved_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} stories marked as issue resolved.')


@admin.register(StoryImage)
class StoryImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'story', 'image',)
    list_filter = ('story',)
    search_fields = ('story__name',)
    autocomplete_fields = ('create_by', 'update_by', 'story')


@admin.register(VerifiedByUser)
class VerifiedByUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'story', 'iteration', 'user', 'total_hour_used')
    list_filter = ('user','iteration')
    search_fields = ('story__id', 'user__fullname', 'user__email', 'user__username')
    autocomplete_fields = ('create_by', 'update_by', 'story', 'iteration', 'user')