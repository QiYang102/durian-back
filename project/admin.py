from django.contrib import admin

from project.models import Project


# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'team', 'name')
    list_filter = ('team',)
    search_fields = ('name',)
    autocomplete_fields = ('create_by', 'update_by', 'team')