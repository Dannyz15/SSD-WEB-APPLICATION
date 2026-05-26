from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuditLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'phone', 'department')}),
    )
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'username_attempted', 'action', 'resource', 'ip_address', 'success']
    list_filter = ['action', 'success']
    search_fields = ['user__username', 'username_attempted', 'ip_address']
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
