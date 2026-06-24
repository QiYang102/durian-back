from django.conf import settings
from django.contrib import admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin


from .models import Tenant, User, Feature, FeatureAccess

admin.site.site_header = f'{settings.PROJECT_NAME} - Admin Panel | v{settings.PROJECT_VERSION}-{settings.PROJECT_ENVIRONMENT}'
admin.site.site_title = f'{settings.PROJECT_NAME} - Admin Panel'
admin.site.register(Feature)


class UserChangeForm(DjangoUserChangeForm):
    """
    A form for updating users, includes all the fields on the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(label='Password',
                                         help_text=("Raw passwords are not stored, so there is no way to see "
                                                    "this user's password, but you can change the password "
                                                    "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = User
        fields = '__all__'

    def clean_password(self):
        """
        As password field is read-only, we will discard whatever user fill in, and load with initial value.
        """
        return self.initial['password']


class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 0
    readonly_fields = ('code', 'name',)
    fields = ('code', 'name', 'is_active')
    ordering = ('id',)


class FeatureAccessInline(admin.TabularInline):
    model = FeatureAccess
    extra = 0
    # readonly_fields = ('feature__code', 'feature__name',)
    fields = ('feature',)
    ordering = ('id',)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    inlines = [FeatureInline]
    readonly_fields = ('create_at', 'update_at',)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'fullname', 'role', 'is_active', 'is_verify', 'msisdn', 'mobile_prefix', 'mobile_number', 'capacity', 'image',)
    list_filter = ('role',)
    search_fields = ('username', 'fullname', 'mobile_number', 'msisdn')
    readonly_fields = ('update_at', 'msisdn')
    form = UserChangeForm
    inlines = [FeatureAccessInline]
    autocomplete_fields = ('create_by', 'update_by')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'tenant')}
         ),
    )


fieldsets_list = list(filter(lambda item: item[0] != 'Personal info', UserAdmin.fieldsets))
fieldsets_list.insert(1, ('Personal info', {'fields': ('email', 'fullname', 'msisdn', 'mobile_prefix', 'mobile_number', 'role', 'is_verify', 'device_token',
                                                       'create_by', 'update_by', 'update_at', 'capacity','image')}), )


UserAdmin.fieldsets = fieldsets_list


class ReadonlyInline(admin.TabularInline):
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
