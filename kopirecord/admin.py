from django.contrib import admin

from kopirecord.models import KopiRecord

# Register your models here.

@admin.register(KopiRecord)
class KopiRecordAdmin(admin.ModelAdmin):
    list_display = ('member_name', 'remark', 'amount', 'status', 'create_date', 'complete_date', 'iteration')
    list_filter = ('member_name', )
    search_fields = ('member_name', )
    readonly_fields = ()
    autocomplete_fields = ('member_name', 'create_by', 'update_by', 'iteration')