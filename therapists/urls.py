# therapists/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.therapist_list, name='therapist_list'),
    path('<int:pk>/', views.therapist_detail, name='therapist_detail'),
    path('appointments/', views.user_appointments, name='user_appointments'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
]


