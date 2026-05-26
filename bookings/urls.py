from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Resources
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/new/', views.resource_create, name='resource_create'),
    path('resources/<uuid:pk>/edit/', views.resource_update, name='resource_update'),
    path('resources/<uuid:pk>/delete/', views.resource_delete, name='resource_delete'),

    # Bookings
    path('list/', views.booking_list, name='booking_list'),
    path('new/', views.booking_create, name='booking_create'),
    path('<uuid:pk>/', views.booking_detail, name='booking_detail'),
    path('<uuid:pk>/edit/', views.booking_update, name='booking_update'),
    path('<uuid:pk>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('<uuid:pk>/review/', views.booking_review, name='booking_review'),
]
