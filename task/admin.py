from django.contrib import admin
from core.models import User

from task.models import Task, TaskHour, TaskImage, TaskTemplate, TaskTemplateItem

# Register your models here.
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id','description','due_date','is_bug','estimate_time', 'total_hour_used', 'status', 'iteration', 'story', 'user', 'update_at', 'assigned_at')
    list_filter = ('status', 'iteration', 'user', 'is_bug',)
    search_fields = ('description', 'story__id', )
    readonly_fields = ('total_hour_used',)
    autocomplete_fields = ('user', 'create_by', 'update_by', 'story', 'iteration')

@admin.register(TaskHour)
class TaskHourAdmin(admin.ModelAdmin):
    list_display = ('id','hour', 'remain_hour','status','user', 'task', 'update_at')
    list_filter = ('user', )
    search_fields = ('user__fullname', 'user__email', 'user__username', 'task__id')
    autocomplete_fields = ('user', 'create_by', 'update_by', 'task')

@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'image', 'update_at')
    list_filter = ('task', )
    search_fields = ('task__id', 'image')
    autocomplete_fields = ('create_by', 'update_by', 'task')

@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')
    autocomplete_fields = ('create_by', 'update_by')

@admin.register(TaskTemplateItem)
class TaskTemplateItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'task_template', 'ordering', 'estimate_time')
    list_filter = ('task_template', )
    search_fields = ('id', 'task_template')
    autocomplete_fields = ('create_by', 'update_by', 'task_template')