import os
from wsgiref.util import FileWrapper

from django.contrib import admin
from django.urls import path, reverse
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.shortcuts import render
from django import forms

from core.excel import ExcelExport
from core.utility import tenant_from_request
from eventcalendar.models import EventCalendar
from eventcalendar import eventcalendar_service

# Register your models here.

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(EventCalendar)
class IterationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'start_date', 'end_date', 'description', 'user', 'total_days')
    list_filter = ('type', 'user')
    search_fields = ('user', )
    readonly_fields = ()
    autocomplete_fields = ('user', 'create_by', 'update_by')

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
            messages.success(request, 'Upload completed (%s)')

            tenant = tenant_from_request(request)
            model_created_count = eventcalendar_service.import_event_calendar_csv_file(csv_file, tenant)

            result = dict(model_created=model_created_count)
            messages.success(request, 'Upload completed (%s)' % result)

            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/eventcalendar_upload.html", data)
    
    def download_template_file(self, request):
        export = ExcelExport()

        template_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'import_eventcalendar_csv_sample.csv')

        file = open(template_file, 'rb')
        download_filename = '{0}.csv'.format('import_eventcalendar_csv_sample')

        response = HttpResponse(FileWrapper(file), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = export.rfc5987_content_disposition(download_filename)

        return response