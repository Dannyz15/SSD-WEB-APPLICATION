import io
import os
import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.validators import RegexValidator
from PIL import Image
from .models import User

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_PROFILE_PIC_SIZE = 2 * 1024 * 1024  # 2 MB

phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message='Enter a valid phone number (9–15 digits, optional leading +).',
)

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Username may only contain letters, digits, and @/./+/-/_',
)


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        username_validator(username)
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            phone_validator(phone)
        return phone

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if name and not re.match(r'^[A-Za-z\s\-\']+$', name):
            raise forms.ValidationError('First name may only contain letters, spaces, hyphens, and apostrophes.')
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if name and not re.match(r'^[A-Za-z\s\-\']+$', name):
            raise forms.ValidationError('Last name may only contain letters, spaces, hyphens, and apostrophes.')
        return name

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Password must contain at least one digit.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError('Password must contain at least one special character.')
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class SecureLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if len(username) > 150:
            raise forms.ValidationError('Invalid username.')
        return username


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            phone_validator(phone)
        return phone

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if name and not re.match(r'^[A-Za-z\s\-\']+$', name):
            raise forms.ValidationError('First name may only contain letters, spaces, hyphens, and apostrophes.')
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if name and not re.match(r'^[A-Za-z\s\-\']+$', name):
            raise forms.ValidationError('Last name may only contain letters, spaces, hyphens, and apostrophes.')
        return name

    def clean_profile_picture(self):
        file = self.cleaned_data.get('profile_picture')
        if not file or not hasattr(file, 'name'):
            return file

        # Validate file size (max 2 MB)
        if file.size > MAX_PROFILE_PIC_SIZE:
            raise forms.ValidationError('Profile picture must be under 2 MB.')

        # Validate file extension (whitelist)
        ext = os.path.splitext(file.name)[1].lstrip('.').lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise forms.ValidationError('Only JPG, PNG, and GIF images are allowed.')

        # Validate actual image content via Pillow (checks magic bytes, not just extension)
        try:
            img = Image.open(io.BytesIO(file.read()))
            img.verify()
        except Exception:
            raise forms.ValidationError('Uploaded file is not a valid image.')

        file.seek(0)
        return file


class SecurePasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1', '')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Password must contain at least one digit.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError('Password must contain at least one special character.')
        return password
