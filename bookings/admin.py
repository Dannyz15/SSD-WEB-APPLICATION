from django.contrib import admin
from .models import Resource, Booking


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'resource_type', 'location', 'capacity', 'is_active']
    list_filter = ['resource_type', 'is_active']
    search_fields = ['name', 'location']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'resource', 'start_datetime', 'end_datetime', 'status']
    list_filter = ['status', 'resource']
    search_fields = ['title', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
