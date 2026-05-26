import re
from django import forms
from django.utils import timezone
from .models import Resource, Booking


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'resource_type', 'location', 'capacity', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not re.match(r'^[\w\s\-\(\)]+$', name):
            raise forms.ValidationError('Resource name contains invalid characters.')
        if len(name) < 2:
            raise forms.ValidationError('Resource name must be at least 2 characters.')
        return name

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError('Capacity must be at least 1.')
        if capacity is not None and capacity > 10000:
            raise forms.ValidationError('Capacity cannot exceed 10,000.')
        return capacity

    def clean_location(self):
        location = self.cleaned_data.get('location', '').strip()
        if location and len(location) > 200:
            raise forms.ValidationError('Location is too long (max 200 characters).')
        return location


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['resource', 'title', 'purpose', 'start_datetime', 'end_datetime', 'attendees']
        widgets = {
            'resource': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_datetime': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'end_datetime': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'attendees': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resource'].queryset = Resource.objects.filter(is_active=True)
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not re.match(r'^[\w\s\-\(\)\.,!]+$', title):
            raise forms.ValidationError('Title contains invalid characters.')
        if len(title) < 3:
            raise forms.ValidationError('Title must be at least 3 characters.')
        return title

    def clean_purpose(self):
        purpose = self.cleaned_data.get('purpose', '').strip()
        if len(purpose) < 10:
            raise forms.ValidationError('Please provide a more detailed purpose (at least 10 characters).')
        if len(purpose) > 1000:
            raise forms.ValidationError('Purpose is too long (max 1000 characters).')
        return purpose

    def clean_attendees(self):
        attendees = self.cleaned_data.get('attendees')
        if attendees is not None and attendees < 1:
            raise forms.ValidationError('Attendees must be at least 1.')
        if attendees is not None and attendees > 10000:
            raise forms.ValidationError('Attendees cannot exceed 10,000.')
        return attendees

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_datetime')
        end = cleaned.get('end_datetime')
        resource = cleaned.get('resource')
        attendees = cleaned.get('attendees')

        if start and end:
            if start <= timezone.now():
                self.add_error('start_datetime', 'Start time must be in the future.')
            if end <= start:
                self.add_error('end_datetime', 'End time must be after start time.')
            delta = end - start
            if delta.total_seconds() > 24 * 3600:
                self.add_error('end_datetime', 'Booking duration cannot exceed 24 hours.')

        if resource and attendees and attendees > resource.capacity:
            self.add_error('attendees', f'Attendees exceed resource capacity ({resource.capacity}).')

        return cleaned


class BookingStatusForm(forms.ModelForm):
    """Admin use: approve or reject a booking."""
    class Meta:
        model = Booking
        fields = ['status', 'admin_note']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_admin_note(self):
        note = self.cleaned_data.get('admin_note', '').strip()
        if len(note) > 500:
            raise forms.ValidationError('Note is too long (max 500 characters).')
        return note
