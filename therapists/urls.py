from django.urls import path
from . import views

app_name = 'therapists'

urlpatterns = [
    # Therapist listing and search
    path('', views.therapist_list, name='therapist_list'),
    path('<int:therapist_id>/', views.therapist_detail, name='therapist_detail'),
    path('search/', views.therapist_list, name='therapist_search'),
    
    # Therapist authentication and onboarding
    path('signup/', views.therapist_signup, name='therapist_signup'),
    path('login/', views.CustomLoginView.as_view(), name='therapist_login'),
    
    # Therapist dashboard and management
    path('dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    path('dashboard/appointments/', views.therapist_appointments, name='therapist_appointments'),
    path('dashboard/profile/', views.update_therapist_profile, name='update_therapist_profile'),
    path('dashboard/schedule/', views.manage_schedule, name='manage_schedule'),
    
    # Appointment booking and management
    path('<int:therapist_id>/book/', views.book_appointment, name='book_appointment'),
    path('appointment/<uuid:appointment_id>/success/', views.booking_success, name='booking_success'),
    path('appointment/<uuid:appointment_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('appointment/<uuid:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointment/<uuid:appointment_id>/messages/', views.appointment_messages, name='appointment_messages'),
    
    # Reviews and ratings
    path('appointment/<uuid:appointment_id>/review/', views.leave_review, name='leave_review'),
    path('review/<int:review_id>/respond/', views.respond_to_review, name='respond_to_review'),
    
    # Patient profile management
    path('profile/update/', views.update_patient_profile, name='update_patient_profile'),
    
    # API endpoints
    path('api/availability/<int:therapist_id>/', views.get_availability, name='get_availability'),
    path('api/appointment/<uuid:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
]