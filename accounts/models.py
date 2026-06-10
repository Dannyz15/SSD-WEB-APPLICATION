import os
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def profile_picture_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'profile_pictures/{uuid.uuid4().hex}{ext}'


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to=profile_picture_path,
        null=True,
        blank=True,
    )

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'


class AuditLog(models.Model):
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_LOGIN_FAILED = 'LOGIN_FAILED'
    ACTION_REGISTER = 'REGISTER'
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_VIEW = 'VIEW'
    ACTION_PROFILE_UPDATE = 'PROFILE_UPDATE'
    ACTION_PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    ACTION_ACCESS_DENIED = 'ACCESS_DENIED'

    ACTION_CHOICES = [
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_LOGIN_FAILED, 'Failed Login'),
        (ACTION_REGISTER, 'Register'),
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_VIEW, 'View'),
        (ACTION_PROFILE_UPDATE, 'Profile Update'),
        (ACTION_PASSWORD_CHANGE, 'Password Change'),
        (ACTION_ACCESS_DENIED, 'Access Denied'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    username_attempted = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    extra = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor = self.user.username if self.user else self.username_attempted or 'anonymous'
        return f'[{self.timestamp:%Y-%m-%d %H:%M}] {actor} — {self.action}'
