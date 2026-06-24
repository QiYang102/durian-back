from django.contrib import admin

from team.models import Team, TeamMember

# Register your models here.
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active', )
    search_fields = ('name', )
    autocomplete_fields = ('create_by', 'update_by')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('team', 'user')
    list_filter = ('is_active', 'team')
    search_fields = ('name', )
    autocomplete_fields = ('user', 'create_by', 'update_by', 'team')
