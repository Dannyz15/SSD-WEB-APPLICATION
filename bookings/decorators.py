from functools import wraps
from django.shortcuts import render
from accounts.models import AuditLog
from accounts.utils import log_audit


def admin_required(view_func):
    """Restrict view to admin-role users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            from django.shortcuts import redirect
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not request.user.is_admin_user():
            log_audit(request, AuditLog.ACTION_ACCESS_DENIED, resource=request.path, success=False)
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
