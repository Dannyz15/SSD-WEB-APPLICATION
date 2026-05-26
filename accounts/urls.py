from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_update_view, name='profile_edit'),
    path('profile/password/', views.password_change_view, name='password_change'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
]
