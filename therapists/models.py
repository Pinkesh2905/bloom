from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone as django_timezone  # Rename the import to avoid conflict
from datetime import timedelta
import uuid

class TherapistProfile(models.Model):
    """Enhanced therapist profile with comprehensive information"""
    SPECIALIZATION_CHOICES = [
        ('CBT', 'Cognitive Behavioral Therapy'),
        ('DBT', 'Dialectical Behavior Therapy'),
        ('PSYCHODYNAMIC', 'Psychodynamic Therapy'),
        ('HUMANISTIC', 'Humanistic Therapy'),
        ('FAMILY_THERAPY', 'Family Therapy'),
        ('COUPLES_THERAPY', 'Couples Therapy'),
        ('ADDICTION', 'Addiction Counseling'),
        ('TRAUMA', 'Trauma Therapy'),
        ('ANXIETY', 'Anxiety Disorders'),
        ('DEPRESSION', 'Depression Treatment'),
        ('GRIEF', 'Grief Counseling'),
        ('EATING_DISORDERS', 'Eating Disorders'),
        ('ADOLESCENT', 'Adolescent Therapy'),
        ('GERIATRIC', 'Geriatric Psychology'),
        ('GROUP_THERAPY', 'Group Therapy'),
        ('MINDFULNESS', 'Mindfulness-Based Therapy'),
        ('EMDR', 'EMDR Therapy'),
        ('ART_THERAPY', 'Art Therapy'),
        ('MUSIC_THERAPY', 'Music Therapy'),
        ('SOMATIC', 'Somatic Therapy'),
    ]
    
    LANGUAGE_CHOICES = [
        ('EN', 'English'),
        ('ES', 'Spanish'),
        ('FR', 'French'),
        ('DE', 'German'),
        ('IT', 'Italian'),
        ('PT', 'Portuguese'),
        ('RU', 'Russian'),
        ('ZH', 'Chinese'),
        ('JA', 'Japanese'),
        ('AR', 'Arabic'),
        ('HI', 'Hindi'),
        ('KO', 'Korean'),
    ]
    
    QUALIFICATION_CHOICES = [
        ('PHD', 'Ph.D. in Psychology'),
        ('PSYD', 'Psy.D. in Clinical Psychology'),
        ('MSW', 'Master of Social Work'),
        ('MS_COUNSELING', 'M.S. in Counseling'),
        ('MA_PSYCHOLOGY', 'M.A. in Psychology'),
        ('LCSW', 'Licensed Clinical Social Worker'),
        ('LPC', 'Licensed Professional Counselor'),
        ('LMFT', 'Licensed Marriage and Family Therapist'),
        ('LPCC', 'Licensed Professional Clinical Counselor'),
        ('PSYCHIATRIC_NURSE', 'Psychiatric Mental Health Nurse Practitioner'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='therapist_profile')
    license_number = models.CharField(max_length=50, help_text="Professional license number")
    specializations = models.JSONField(default=list, help_text="List of specializations")
    qualifications = models.JSONField(default=list, help_text="Educational qualifications")
    languages_spoken = models.JSONField(default=list, help_text="Languages spoken")
    
    bio = models.TextField(help_text="Professional biography (max 1000 characters)", max_length=1000)
    years_experience = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(60)])
    profile_picture = models.ImageField(upload_to='therapist_pics/', default='therapist_pics/default.png')
    
    # Pricing and availability
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    session_duration = models.IntegerField(default=60, help_text="Session duration in minutes")
    accepts_insurance = models.BooleanField(default=False)
    insurance_providers = models.JSONField(default=list, blank=True)
    
    # Contact and location
    phone_number = models.CharField(max_length=20, blank=True)
    office_address = models.TextField(blank=True, help_text="Office address for in-person sessions")
    timezone = models.CharField(max_length=50, default='UTC')  # This field name conflicts with the import
    
    # Platform settings
    offers_video_sessions = models.BooleanField(default=True)
    offers_chat_sessions = models.BooleanField(default=True)
    offers_phone_sessions = models.BooleanField(default=False)
    offers_in_person = models.BooleanField(default=False)
    
    # Verification and approval
    is_verified = models.BooleanField(default=False, help_text="Email and identity verified")
    is_approved = models.BooleanField(default=False, help_text="Admin approved to accept patients")
    license_verified = models.BooleanField(default=False, help_text="Professional license verified")
    background_check_completed = models.BooleanField(default=False)
    
    # Statistics
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    response_time_hours = models.IntegerField(default=24, help_text="Average response time in hours")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(default=django_timezone.now)  # Fixed: use django_timezone.now and renamed field
    
    # Profile completeness
    profile_complete = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'therapist_profiles'
        indexes = [
            models.Index(fields=['is_approved', 'is_verified']),
            models.Index(fields=['rating']),
            models.Index(fields=['hourly_rate']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def specializations_display(self):
        """Return formatted specializations for display"""
        spec_dict = dict(self.SPECIALIZATION_CHOICES)
        return [spec_dict.get(spec, spec) for spec in self.specializations]
    
    @property
    def languages_display(self):
        """Return formatted languages for display"""
        lang_dict = dict(self.LANGUAGE_CHOICES)
        return [lang_dict.get(lang, lang) for lang in self.languages_spoken]
    
    def get_available_session_types(self):
        """Return list of available session types"""
        types = []
        if self.offers_video_sessions:
            types.append(('VIDEO', 'Video Session'))
        if self.offers_chat_sessions:
            types.append(('CHAT', 'Chat Session'))
        if self.offers_phone_sessions:
            types.append(('PHONE', 'Phone Session'))
        if self.offers_in_person:
            types.append(('IN_PERSON', 'In-Person Session'))
        return types
    
    def calculate_profile_completeness(self):
        """Calculate and update profile completeness percentage"""
        total_fields = 15
        completed_fields = 0
        
        required_fields = [
            self.bio, self.license_number, self.years_experience,
            self.hourly_rate, self.specializations, self.qualifications,
            self.languages_spoken
        ]
        
        for field in required_fields:
            if field:
                completed_fields += 1
        
        # Check boolean fields
        if self.profile_picture and self.profile_picture.name != 'therapist_pics/default.png':
            completed_fields += 1
        if self.phone_number:
            completed_fields += 1
        if any([self.offers_video_sessions, self.offers_chat_sessions, 
               self.offers_phone_sessions, self.offers_in_person]):
            completed_fields += 1
        
        # Additional fields
        if self.office_address:
            completed_fields += 1
        if self.insurance_providers:
            completed_fields += 1
        if self.timezone != 'UTC':
            completed_fields += 1
        if self.session_duration != 60:
            completed_fields += 1
        if self.is_verified:
            completed_fields += 1
        
        percentage = (completed_fields / total_fields) * 100
        self.profile_complete = percentage >= 80
        return percentage

class TherapistSchedule(models.Model):
    """Therapist availability schedule"""
    WEEKDAYS = [
        (0, 'Monday'),
        (1, 'Tuesday'), 
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    therapist = models.ForeignKey(TherapistProfile, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    break_start = models.TimeField(null=True, blank=True, help_text="Break start time")
    break_end = models.TimeField(null=True, blank=True, help_text="Break end time")
    
    class Meta:
        unique_together = ['therapist', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.therapist.full_name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

class Appointment(models.Model):
    """Enhanced appointment model with comprehensive tracking"""
    SESSION_TYPE_CHOICES = [
        ('VIDEO', 'Video Session'),
        ('CHAT', 'Chat Session'),
        ('PHONE', 'Phone Session'),
        ('IN_PERSON', 'In-Person Session'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED_BY_PATIENT', 'Cancelled by Patient'),
        ('CANCELLED_BY_THERAPIST', 'Cancelled by Therapist'),
        ('NO_SHOW_PATIENT', 'Patient No-Show'),
        ('NO_SHOW_THERAPIST', 'Therapist No-Show'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    
    CANCELLATION_REASON_CHOICES = [
        ('EMERGENCY', 'Emergency'),
        ('ILLNESS', 'Illness'),
        ('SCHEDULE_CONFLICT', 'Schedule Conflict'),
        ('PERSONAL', 'Personal Reasons'),
        ('TECHNICAL', 'Technical Issues'),
        ('OTHER', 'Other'),
    ]

    # Core appointment details
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    therapist = models.ForeignKey(TherapistProfile, on_delete=models.CASCADE, related_name='therapist_appointments')
    
    # Scheduling
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(default=60, help_text="Duration in minutes")
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Session details
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='VIDEO')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    
    # Communication
    patient_notes = models.TextField(blank=True, help_text="Notes from patient")
    therapist_notes = models.TextField(blank=True, help_text="Private therapist notes")
    session_summary = models.TextField(blank=True, help_text="Session summary")
    
    # Technical details
    session_link = models.URLField(blank=True, help_text="Video session link")
    session_room_id = models.CharField(max_length=100, blank=True)
    recording_consent = models.BooleanField(default=False)
    
    # Financial
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='PENDING')
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Cancellation and rescheduling
    cancellation_reason = models.CharField(max_length=20, choices=CANCELLATION_REASON_CHOICES, blank=True)
    cancellation_details = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_appointments')
    
    rescheduled_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rescheduled_appointments')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    reminder_sent = models.BooleanField(default=False)
    confirmation_sent = models.BooleanField(default=False)
    follow_up_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'appointments'
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['therapist', 'status']),
            models.Index(fields=['date', 'time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Appointment {self.id} - {self.therapist.full_name} & {self.patient.get_full_name()} on {self.date} at {self.time}"
    
    @property
    def appointment_datetime(self):
        """Backward compatibility property"""
        from datetime import datetime
        return datetime.combine(self.date, self.time)
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled (24h+ notice)"""
        from datetime import datetime, timedelta
        appointment_datetime = datetime.combine(self.date, self.time)
        return datetime.now() + timedelta(hours=24) <= appointment_datetime
    
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled"""
        return self.status in ['PENDING', 'CONFIRMED'] and self.can_be_cancelled()
    
    def get_duration_display(self):
        """Format duration for display"""
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours:
            return f"{hours}h {minutes}m" if minutes else f"{hours}h"
        return f"{minutes}m"

class TherapistReview(models.Model):
    """Patient reviews for therapists"""
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_reviews')
    therapist = models.ForeignKey(TherapistProfile, on_delete=models.CASCADE, related_name='reviews')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(max_length=1000, blank=True)
    
    # Specific rating categories
    communication_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    professionalism_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    effectiveness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    would_recommend = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    therapist_response = models.TextField(blank=True, help_text="Therapist's response to review")
    responded_at = models.DateTimeField(null=True, blank=True)
    
    helpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'therapist_reviews'
        ordering = ['-created_at']
        unique_together = ['patient', 'appointment']

    def __str__(self):
        return f"Review by {self.patient.get_full_name()} for {self.therapist.full_name} - {self.rating}/5"

class AppointmentMessage(models.Model):
    """Messages exchanged between patient and therapist regarding appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_appointment_messages')
    content = models.TextField()
    
    is_system_message = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    
    # AI assistance
    ai_generated = models.BooleanField(default=False, help_text="Message generated by AI assistant")
    ai_confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    
    # File attachments
    attachment = models.FileField(upload_to='appointment_attachments/', null=True, blank=True)
    attachment_type = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'appointment_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in appointment {self.appointment.id}"

class PatientProfile(models.Model):
    """Enhanced patient profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    
    # Basic info
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Medical information
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_id = models.CharField(max_length=50, blank=True)
    medical_conditions = models.TextField(blank=True, help_text="Current medical conditions")
    medications = models.TextField(blank=True, help_text="Current medications")
    
    # Therapy preferences
    preferred_therapist_gender = models.CharField(max_length=20, blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('N', 'Non-binary'), ('ANY', 'No preference')])
    preferred_session_type = models.CharField(max_length=20, blank=True, choices=Appointment.SESSION_TYPE_CHOICES)
    therapy_goals = models.TextField(blank=True, help_text="What you hope to achieve")
    
    # Platform preferences
    notifications_enabled = models.BooleanField(default=True)
    email_reminders = models.BooleanField(default=True)
    sms_reminders = models.BooleanField(default=False)
    
    # Privacy settings
    profile_visibility = models.CharField(max_length=20, default='THERAPISTS_ONLY', choices=[
        ('PRIVATE', 'Private'),
        ('THERAPISTS_ONLY', 'Therapists Only'),
        ('PUBLIC', 'Public'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patient_profiles'

    def __str__(self):
        return f"Patient Profile - {self.user.get_full_name()}"

# Legacy model alias for backward compatibility
Therapist = TherapistProfile

# Signals for automatic profile creation and updates
@receiver(post_save, sender=User)
def create_patient_profile(sender, instance, created, **kwargs):
    """Create patient profile when user is created"""
    if created and not hasattr(instance, 'therapist_profile'):
        PatientProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=TherapistReview)
def update_therapist_rating(sender, instance, created, **kwargs):
    """Update therapist rating when new review is added"""
    if created:
        from django.db.models import Avg
        therapist = instance.therapist
        reviews = TherapistReview.objects.filter(therapist=therapist)
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        
        therapist.rating = round(avg_rating, 2) if avg_rating else 0.00
        therapist.total_reviews = reviews.count()
        therapist.save(update_fields=['rating', 'total_reviews'])

@receiver(post_save, sender=Appointment)
def update_session_count(sender, instance, created, **kwargs):
    """Update therapist session count when appointment is completed"""
    if not created and instance.status == 'COMPLETED':
        therapist = instance.therapist
        therapist.total_sessions = Appointment.objects.filter(
            therapist=therapist, 
            status='COMPLETED'
        ).count()
        therapist.save(update_fields=['total_sessions'])