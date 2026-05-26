import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from accounts.models import AuditLog
from accounts.utils import log_audit
from .decorators import admin_required
from .forms import ResourceForm, BookingForm, BookingStatusForm
from .models import Resource, Booking

logger = logging.getLogger('bookings')


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
@never_cache
def dashboard(request):
    user = request.user
    if user.is_admin_user():
        pending_count = Booking.objects.filter(status=Booking.STATUS_PENDING).count()
        total_bookings = Booking.objects.count()
        total_resources = Resource.objects.filter(is_active=True).count()
        recent_bookings = Booking.objects.select_related('user', 'resource').all()[:10]
        context = {
            'pending_count': pending_count,
            'total_bookings': total_bookings,
            'total_resources': total_resources,
            'recent_bookings': recent_bookings,
        }
    else:
        my_bookings = Booking.objects.filter(user=user).select_related('resource')[:10]
        context = {'my_bookings': my_bookings}

    return render(request, 'bookings/dashboard.html', context)


# ─── Resources (Admin only) ───────────────────────────────────────────────────

@login_required
@never_cache
def resource_list(request):
    resources = Resource.objects.all()
    return render(request, 'bookings/resource_list.html', {'resources': resources})


@admin_required
@never_cache
@require_http_methods(['GET', 'POST'])
def resource_create(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.created_by = request.user
            resource.save()
            log_audit(request, AuditLog.ACTION_CREATE, resource=f'Resource:{resource.id}')
            messages.success(request, f'Resource "{resource.name}" created.')
            return redirect('bookings:resource_list')
    else:
        form = ResourceForm()
    return render(request, 'bookings/resource_form.html', {'form': form, 'action': 'Create'})


@admin_required
@never_cache
@require_http_methods(['GET', 'POST'])
def resource_update(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if request.method == 'POST':
        form = ResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            log_audit(request, AuditLog.ACTION_UPDATE, resource=f'Resource:{pk}')
            messages.success(request, f'Resource "{resource.name}" updated.')
            return redirect('bookings:resource_list')
    else:
        form = ResourceForm(instance=resource)
    return render(request, 'bookings/resource_form.html', {'form': form, 'action': 'Edit', 'resource': resource})


@admin_required
@require_http_methods(['POST'])
def resource_delete(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    name = resource.name
    resource.delete()
    log_audit(request, AuditLog.ACTION_DELETE, resource=f'Resource:{pk}')
    messages.success(request, f'Resource "{name}" deleted.')
    return redirect('bookings:resource_list')


# ─── Bookings ─────────────────────────────────────────────────────────────────

@login_required
@never_cache
def booking_list(request):
    user = request.user
    if user.is_admin_user():
        bookings = Booking.objects.select_related('user', 'resource').all()
    else:
        bookings = Booking.objects.filter(user=user).select_related('resource')

    status_filter = request.GET.get('status', '').strip()
    valid_statuses = [s[0] for s in Booking.STATUS_CHOICES]
    if status_filter in valid_statuses:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'bookings/booking_list.html', {
        'bookings': bookings,
        'status_choices': Booking.STATUS_CHOICES,
        'selected_status': status_filter,
    })


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def booking_create(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            log_audit(request, AuditLog.ACTION_CREATE, resource=f'Booking:{booking.id}')
            messages.success(request, 'Booking request submitted.')
            return redirect('bookings:booking_list')
    else:
        form = BookingForm()
    return render(request, 'bookings/booking_form.html', {'form': form, 'action': 'New'})


@login_required
@never_cache
def booking_detail(request, pk):
    user = request.user
    if user.is_admin_user():
        booking = get_object_or_404(Booking.objects.select_related('user', 'resource'), pk=pk)
    else:
        # Users can only view their own bookings (prevent IDOR)
        booking = get_object_or_404(Booking.objects.select_related('resource'), pk=pk, user=user)

    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def booking_update(request, pk):
    user = request.user
    booking = get_object_or_404(Booking, pk=pk, user=user)

    if booking.status != Booking.STATUS_PENDING:
        messages.error(request, 'Only pending bookings can be edited.')
        return redirect('bookings:booking_detail', pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            log_audit(request, AuditLog.ACTION_UPDATE, resource=f'Booking:{pk}')
            messages.success(request, 'Booking updated.')
            return redirect('bookings:booking_detail', pk=pk)
    else:
        form = BookingForm(instance=booking)
    return render(request, 'bookings/booking_form.html', {'form': form, 'action': 'Edit', 'booking': booking})


@login_required
@require_http_methods(['POST'])
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status not in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED):
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', pk=pk)
    booking.status = Booking.STATUS_CANCELLED
    booking.save()
    log_audit(request, AuditLog.ACTION_UPDATE, resource=f'Booking:{pk}', extra='Cancelled by user')
    messages.success(request, 'Booking cancelled.')
    return redirect('bookings:booking_list')


# ─── Admin: review bookings ───────────────────────────────────────────────────

@admin_required
@never_cache
@require_http_methods(['GET', 'POST'])
def booking_review(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('user', 'resource'), pk=pk)

    if request.method == 'POST':
        form = BookingStatusForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            log_audit(
                request,
                AuditLog.ACTION_UPDATE,
                resource=f'Booking:{pk}',
                extra=f'Status set to {booking.status}',
            )
            messages.success(request, f'Booking status updated to {booking.get_status_display()}.')
            return redirect('bookings:booking_list')
    else:
        form = BookingStatusForm(instance=booking)

    return render(request, 'bookings/booking_review.html', {'form': form, 'booking': booking})
