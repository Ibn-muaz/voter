from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import INECUser, UserSession


@admin.register(INECUser)
class INECUserAdmin(UserAdmin):
    """
    Admin interface for INEC users with custom fields.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'employee_id', 'state', 'is_active_officer', 'is_active')
    list_filter = ('role', 'state', 'lga', 'is_active_officer', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('INEC Information', {
            'fields': ('role', 'state', 'lga', 'employee_id', 'is_active_officer')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('INEC Information', {
            'fields': ('role', 'state', 'lga', 'employee_id', 'is_active_officer')
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for user sessions.
    """
    list_display = ('user', 'ip_address', 'login_time', 'logout_time', 'is_active')
    list_filter = ('is_active', 'login_time', 'logout_time')
    search_fields = ('user__username', 'user__employee_id', 'ip_address')
    readonly_fields = ('session_key', 'login_time')
    ordering = ('-login_time',)