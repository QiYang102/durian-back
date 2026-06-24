from django.contrib import admin

from .models import Season
from .utils import generate_month_report


@admin.action(description="Generate season report")
def action_generate_month_report(modeladmin, request, queryset):
    count = 0
    for season in queryset:
        generate_month_report(
            season.start_date,
            season.end_date,
            season
        )
        count += 1

    modeladmin.message_user(
        request,
        f"Successfully generated reports for {count} season(s)."
    )


@admin.register(Season)
class SeasonSessionAdmin(admin.ModelAdmin):
    list_display = ("season_name", "team", "start_date", "end_date")
    list_filter = ("team", "start_date", "end_date")
    search_fields = ("season_name", "team__name")
    readonly_fields = ("report_data",)
    actions = [action_generate_month_report]
