import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Resource(models.Model):
    """A bookable resource (e.g. meeting room, lab, equipment)."""
    RESOURCE_TYPES = [
        ('room', 'Meeting Room'),
        ('lab', 'Laboratory'),
        ('equipment', 'Equipment'),
        ('hall', 'Hall / Auditorium'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='room')
    location = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_resources',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.get_resource_type_display()})'

    class Meta:
        ordering = ['name']


class Booking(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    title = models.CharField(max_length=200)
    purpose = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    attendees = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} by {self.user.username} [{self.status}]'

    def is_upcoming(self):
        return self.start_datetime > timezone.now()

    def duration_hours(self):
        delta = self.end_datetime - self.start_datetime
        return round(delta.total_seconds() / 3600, 1)
