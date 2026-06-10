import logging
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from .forms import RegistrationForm, SecureLoginForm, ProfileUpdateForm, SecurePasswordChangeForm
from .models import AuditLog
from .utils import log_audit

logger = logging.getLogger('accounts')


@never_cache
@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('bookings:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_audit(request, AuditLog.ACTION_REGISTER, resource='accounts', user=user)
            messages.success(request, 'Account created. Please log in.')
            return redirect('accounts:login')
        else:
            log_audit(
                request,
                AuditLog.ACTION_REGISTER,
                resource='accounts',
                extra='Registration form validation failed',
                success=False,
                username_attempted=request.POST.get('username', ''),
            )
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@never_cache
@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('bookings:dashboard')

    if request.method == 'POST':
        form = SecureLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_audit(request, AuditLog.ACTION_LOGIN, resource='accounts', user=user)
            logger.info('User %s logged in from %s', user.username, request.META.get('REMOTE_ADDR'))
            next_url = request.GET.get('next', '')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('bookings:dashboard')
        else:
            log_audit(
                request,
                AuditLog.ACTION_LOGIN_FAILED,
                resource='accounts',
                extra='Invalid credentials',
                success=False,
                username_attempted=request.POST.get('username', ''),
            )
            logger.warning('Failed login attempt for username "%s"', request.POST.get('username', ''))
    else:
        form = SecureLoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


@login_required
@require_http_methods(['POST'])
def logout_view(request):
    log_audit(request, AuditLog.ACTION_LOGOUT, resource='accounts')
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
@never_cache
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def profile_update_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_audit(request, AuditLog.ACTION_PROFILE_UPDATE, resource='profile')
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def password_change_view(request):
    if request.method == 'POST':
        form = SecurePasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_audit(request, AuditLog.ACTION_PASSWORD_CHANGE, resource='profile')
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:profile')
    else:
        form = SecurePasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
@never_cache
def audit_log_view(request):
    if not request.user.is_admin_user():
        log_audit(request, AuditLog.ACTION_ACCESS_DENIED, resource='audit_log', success=False)
        return render(request, '403.html', status=403)

    logs = AuditLog.objects.select_related('user').all()

    action_filter = request.GET.get('action', '').strip()
    if action_filter and len(action_filter) <= 20:
        logs = logs.filter(action=action_filter)

    logs = logs[:500]

    return render(request, 'accounts/audit_log.html', {
        'logs': logs,
        'action_choices': AuditLog.ACTION_CHOICES,
        'selected_action': action_filter,
    })


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('bookings:dashboard')
    return redirect('accounts:login')


def error_400(request, exception=None):
    return render(request, '400.html', status=400)


def error_403(request, exception=None):
    return render(request, '403.html', status=403)


def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)
