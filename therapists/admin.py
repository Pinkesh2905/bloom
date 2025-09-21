from django.contrib import admin
from .models import (
    TherapistProfile, Appointment, AppointmentMessage, 
    TherapistSchedule, TherapistReview, PatientProfile
)

def approve_therapists(modeladmin, request, queryset):
    """
    Admin action to approve selected therapists.
    """
    queryset.update(is_approved=True)
approve_therapists.short_description = "Approve selected therapists"

def verify_licenses(modeladmin, request, queryset):
    """
    Admin action to verify therapist licenses.
    """
    queryset.update(license_verified=True)
verify_licenses.short_description = "Verify selected therapist licenses"

@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'get_specializations_display', 'is_approved', 'is_verified', 
        'license_verified', 'rating', 'total_sessions', 'created_at'
    )
    list_filter = (
        'is_approved', 'is_verified', 'license_verified', 
        'offers_video_sessions', 'offers_chat_sessions', 
        'accepts_insurance', 'created_at'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name', 
        'license_number', 'bio'
    )
    actions = [approve_therapists, verify_licenses]
    list_editable = ('is_approved', 'is_verified')
    readonly_fields = ('rating', 'total_reviews', 'total_sessions', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_picture')
        }),
        ('Professional Details', {
            'fields': (
                'license_number', 'specializations', 'qualifications', 
                'languages_spoken', 'bio', 'years_experience'
            )
        }),
        ('Pricing & Services', {
            'fields': (
                'hourly_rate', 'session_duration', 'accepts_insurance', 
                'insurance_providers'
            )
        }),
        ('Session Types', {
            'fields': (
                'offers_video_sessions', 'offers_chat_sessions', 
                'offers_phone_sessions', 'offers_in_person'
            )
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'office_address', 'timezone')
        }),
        ('Verification Status', {
            'fields': (
                'is_verified', 'is_approved', 'license_verified', 
                'background_check_completed'
            )
        }),
        ('Statistics', {
            'fields': (
                'rating', 'total_reviews', 'total_sessions', 
                'response_time_hours'
            ),
            'classes': ('collapse',)
        }),
        ('Profile Status', {
            'fields': ('profile_complete', 'onboarding_completed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_specializations_display(self, obj):
        """Display first few specializations"""
        if obj.specializations:
            specs = obj.specializations_display[:3]
            display = ', '.join(specs)
            if len(obj.specializations) > 3:
                display += f' (+{len(obj.specializations) - 3} more)'
            return display
        return "None"
    get_specializations_display.short_description = "Specializations"

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'therapist', 'date', 'time', 
        'status', 'session_type', 'cost'
    )
    list_filter = (
        'status', 'session_type', 'date', 'therapist', 
        'payment_status', 'created_at'
    )
    search_fields = (
        'patient__username', 'patient__first_name', 'patient__last_name',
        'therapist__user__username', 'therapist__user__first_name', 
        'therapist__user__last_name', 'id'
    )
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'confirmed_at', 
        'started_at', 'ended_at'
    )
    date_hierarchy = 'date'
    list_per_page = 25
    
    fieldsets = (
        ('Appointment Details', {
            'fields': (
                'id', 'patient', 'therapist', 'date', 'time', 
                'duration', 'timezone', 'session_type', 'status'
            )
        }),
        ('Session Information', {
            'fields': (
                'session_link', 'session_room_id', 'recording_consent'
            )
        }),
        ('Notes', {
            'fields': ('patient_notes', 'therapist_notes', 'session_summary'),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('cost', 'payment_status', 'payment_method'),
            'classes': ('collapse',)
        }),
        ('Cancellation/Rescheduling', {
            'fields': (
                'cancellation_reason', 'cancellation_details', 
                'cancelled_at', 'cancelled_by', 'rescheduled_from'
            ),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': (
                'reminder_sent', 'confirmation_sent', 'follow_up_sent'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'confirmed_at', 
                'started_at', 'ended_at'
            ),
            'classes': ('collapse',)
        }),
    )

@admin.register(AppointmentMessage)
class AppointmentMessageAdmin(admin.ModelAdmin):
    list_display = (
        'appointment', 'sender', 'created_at', 'is_read', 
        'is_urgent', 'is_system_message', 'ai_generated'
    )
    list_filter = (
        'is_read', 'is_urgent', 'is_system_message', 
        'ai_generated', 'created_at'
    )
    search_fields = (
        'sender__username', 'content', 
        'appointment__id', 'appointment__patient__username'
    )
    readonly_fields = ('created_at', 'read_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Message Details', {
            'fields': (
                'appointment', 'sender', 'content', 'attachment', 
                'attachment_type'
            )
        }),
        ('Message Status', {
            'fields': (
                'is_read', 'is_urgent', 'is_system_message'
            )
        }),
        ('AI Information', {
            'fields': ('ai_generated', 'ai_confidence'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TherapistSchedule)
class TherapistScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'therapist', 'get_day_of_week_display', 'start_time', 
        'end_time', 'is_available'
    )
    list_filter = ('day_of_week', 'is_available', 'therapist')
    search_fields = ('therapist__user__username', 'therapist__user__first_name')
    ordering = ['therapist', 'day_of_week', 'start_time']

@admin.register(TherapistReview)
class TherapistReviewAdmin(admin.ModelAdmin):
    list_display = (
        'therapist', 'patient', 'rating', 'would_recommend', 
        'is_public', 'created_at'
    )
    list_filter = (
        'rating', 'would_recommend', 'is_public', 'is_anonymous', 
        'created_at', 'therapist'
    )
    search_fields = (
        'patient__username', 'therapist__user__username', 
        'review_text', 'therapist_response'
    )
    readonly_fields = ('created_at', 'updated_at', 'responded_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Information', {
            'fields': (
                'patient', 'therapist', 'appointment', 'rating', 
                'review_text'
            )
        }),
        ('Detailed Ratings', {
            'fields': (
                'communication_rating', 'professionalism_rating', 
                'effectiveness_rating'
            ),
            'classes': ('collapse',)
        }),
        ('Review Settings', {
            'fields': (
                'would_recommend', 'is_anonymous', 'is_public', 
                'helpful_count'
            )
        }),
        ('Therapist Response', {
            'fields': ('therapist_response', 'responded_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date_of_birth', 'preferred_session_type', 
        'notifications_enabled', 'created_at'
    )
    list_filter = (
        'preferred_therapist_gender', 'preferred_session_type', 
        'notifications_enabled', 'profile_visibility', 'created_at'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'phone_number', 'insurance_provider'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'date_of_birth', 'phone_number')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Medical Information', {
            'fields': (
                'insurance_provider', 'insurance_id', 
                'medical_conditions', 'medications'
            ),
            'classes': ('collapse',)
        }),
        ('Therapy Preferences', {
            'fields': (
                'preferred_therapist_gender', 'preferred_session_type', 
                'therapy_goals'
            )
        }),
        ('Platform Settings', {
            'fields': (
                'notifications_enabled', 'email_reminders', 
                'sms_reminders', 'profile_visibility'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# TherapistProfile is already registered via the @admin.register decorator above