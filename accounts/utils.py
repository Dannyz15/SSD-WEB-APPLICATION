import logging
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger('accounts')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit(request, action, resource='', extra='', success=True, user=None, username_attempted=''):
    from accounts.models import AuditLog
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:500]
    actor = user or (request.user if request.user.is_authenticated else None)
    AuditLog.objects.create(
        user=actor,
        username_attempted=username_attempted,
        action=action,
        resource=resource,
        ip_address=ip,
        user_agent=ua,
        extra=extra,
        success=success,
    )


def axes_lockout_response(request, credentials, *args, **kwargs):
    """Custom response when django-axes locks out a user."""
    from accounts.models import AuditLog
    log_audit(
        request,
        action=AuditLog.ACTION_LOGIN_FAILED,
        resource='login',
        extra='Account locked after too many failed attempts',
        success=False,
        username_attempted=credentials.get('username', ''),
    )
    return render(request, 'accounts/lockout.html', status=403)
