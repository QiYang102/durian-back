from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'start_date', 'end_date', 'is_live', 'is_active')
    list_filter = ('is_active', 'is_live', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    readonly_fields = ('created_by', 'create_at', 'update_at')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'created_by', 'description')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_live','is_active', 'create_at', 'update_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
            if hasattr(request.user, 'tenant'):
                obj.tenant = request.user.tenant
        super().save_model(request, obj, form, change)