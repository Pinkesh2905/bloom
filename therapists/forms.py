from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, time
import re
from .models import TherapistProfile, Appointment, TherapistSchedule, TherapistReview, PatientProfile, AppointmentMessage

class TherapistSignUpForm(UserCreationForm):
    """Enhanced therapist signup form with comprehensive validation"""
    
    # User fields
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'professional@email.com'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': '+1 (555) 123-4567'
        })
    )
    
    # Professional fields
    license_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Enter your license number'
        })
    )
    specializations = forms.MultipleChoiceField(
        choices=TherapistProfile.SPECIALIZATION_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        help_text="Select all specializations that apply"
    )
    qualifications = forms.MultipleChoiceField(
        choices=TherapistProfile.QUALIFICATION_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        help_text="Select your educational qualifications"
    )
    languages_spoken = forms.MultipleChoiceField(
        choices=TherapistProfile.LANGUAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        help_text="Select languages you can conduct therapy in"
    )
    years_experience = forms.IntegerField(
        min_value=0,
        max_value=60,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Years of experience'
        })
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'rows': 6,
            'placeholder': 'Tell us about your therapeutic approach, experience, and what makes you unique...',
            'maxlength': 1000
        }),
        max_length=1000,
        help_text="Maximum 1000 characters"
    )
    hourly_rate = forms.DecimalField(
        min_value=0,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': '150.00'
        }),
        help_text="Your hourly rate in USD"
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'accept': 'image/*'
        }),
        help_text="Professional headshot (optional)"
    )
    
    # Session preferences
    offers_video_sessions = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput()
    )
    offers_chat_sessions = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput()
    )
    offers_phone_sessions = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput()
    )
    offers_in_person = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput()
    )
    office_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'rows': 3,
            'placeholder': 'Office address for in-person sessions (if applicable)'
        })
    )
    
    # Insurance
    accepts_insurance = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput()
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        
        # CRITICAL FIX 1: Set username from email before validation
        email = cleaned_data.get('email')
        if email:
            cleaned_data['username'] = email
            if User.objects.filter(username=email).exists():
                 self.add_error('email', 'A user with this email already exists.')

        # Ensure at least one session type is offered
        session_types = [
            cleaned_data.get('offers_video_sessions'),
            cleaned_data.get('offers_chat_sessions'),
            cleaned_data.get('offers_phone_sessions'),
            cleaned_data.get('offers_in_person')
        ]
        if not any(session_types):
            # This will become a non_field_error
            raise ValidationError("Please select at least one session type you offer.")
        
        # If offering in-person sessions, office address is required
        if cleaned_data.get('offers_in_person') and not cleaned_data.get('office_address'):
            self.add_error('office_address', "Office address is required for in-person sessions.")
        
        return cleaned_data

    def save(self, commit=True):
        # Create User instance using the parent form's save method
        user = super().save(commit=False)
        
        # CRITICAL FIX 2: Manually set fields not handled by UserCreationForm
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Create the associated TherapistProfile
            TherapistProfile.objects.create(
                user=user,
                license_number=self.cleaned_data['license_number'],
                specializations=self.cleaned_data['specializations'],
                qualifications=self.cleaned_data['qualifications'],
                languages_spoken=self.cleaned_data['languages_spoken'],
                bio=self.cleaned_data['bio'],
                years_experience=self.cleaned_data['years_experience'],
                hourly_rate=self.cleaned_data['hourly_rate'],
                phone_number=self.cleaned_data['phone_number'],
                offers_video_sessions=self.cleaned_data['offers_video_sessions'],
                offers_chat_sessions=self.cleaned_data['offers_chat_sessions'],
                offers_phone_sessions=self.cleaned_data['offers_phone_sessions'],
                offers_in_person=self.cleaned_data['offers_in_person'],
                office_address=self.cleaned_data.get('office_address', ''),
                accepts_insurance=self.cleaned_data['accepts_insurance'],
                profile_picture=self.cleaned_data.get('profile_picture'),
            )
            
        return user

# ... The rest of your forms.py file remains the same ...

class TherapistProfileUpdateForm(forms.ModelForm):
    """Form for therapists to update their profile"""
    
    class Meta:
        model = TherapistProfile
        fields = [
            'bio', 'specializations', 'qualifications', 'languages_spoken',
            'years_experience', 'hourly_rate', 'session_duration', 'phone_number',
            'office_address', 'timezone', 'offers_video_sessions', 'offers_chat_sessions',
            'offers_phone_sessions', 'offers_in_person', 'accepts_insurance',
            'insurance_providers', 'profile_picture'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'text-purple-600'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'
                field.widget.attrs['rows'] = 4
            else:
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'


class AdvancedAppointmentForm(forms.ModelForm):
    """Enhanced appointment booking form with availability checking"""
    
    preferred_dates = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Select up to 3 preferred dates',
            'readonly': True
        }),
        help_text="Click to select your preferred appointment dates"
    )
    
    preferred_times = forms.MultipleChoiceField(
        choices=[
            ('09:00', '9:00 AM'),
            ('10:00', '10:00 AM'),
            ('11:00', '11:00 AM'),
            ('12:00', '12:00 PM'),
            ('13:00', '1:00 PM'),
            ('14:00', '2:00 PM'),
            ('15:00', '3:00 PM'),
            ('16:00', '4:00 PM'),
            ('17:00', '5:00 PM'),
            ('18:00', '6:00 PM'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'text-purple-600'}),
        help_text="Select all times that work for you"
    )
    
    urgency_level = forms.ChoiceField(
        choices=[
            ('LOW', 'Routine - within 2 weeks'),
            ('MEDIUM', 'Moderate - within 1 week'),
            ('HIGH', 'Urgent - within 2-3 days'),
            ('EMERGENCY', 'Emergency - as soon as possible'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'text-purple-600'}),
        initial='LOW'
    )
    
    class Meta:
        model = Appointment
        fields = ['session_type', 'patient_notes']
        
    def __init__(self, therapist=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.therapist = therapist
        
        # Update session type choices based on therapist availability
        if therapist:
            session_choices = therapist.get_available_session_types()
            self.fields['session_type'].choices = session_choices
            
        # Style the form fields
        self.fields['session_type'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'
        })
        self.fields['patient_notes'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'rows': 4,
            'placeholder': 'Please share what you\'d like to discuss and any specific concerns...'
        })
    
    def clean_preferred_dates(self):
        dates_str = self.cleaned_data.get('preferred_dates')
        if not dates_str:
            raise ValidationError("Please select at least one preferred date.")
        
        # Parse dates (assuming format: "2024-01-15,2024-01-16,2024-01-17")
        try:
            date_strings = dates_str.split(',')
            dates = []
            for date_str in date_strings[:3]:  # Max 3 dates
                date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                if date_obj < timezone.now().date():
                    raise ValidationError("Cannot select dates in the past.")
                dates.append(date_obj)
            return dates
        except ValueError:
            raise ValidationError("Invalid date format.")


class AppointmentRescheduleForm(forms.Form):
    """Form for rescheduling appointments"""
    
    new_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'min': timezone.now().date().isoformat()
        })
    )
    new_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'
        })
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'rows': 3,
            'placeholder': 'Please explain why you need to reschedule...'
        }),
        required=False
    )


class AppointmentCancelForm(forms.Form):
    """Form for cancelling appointments"""
    
    cancellation_reason = forms.ChoiceField(
        choices=Appointment.CANCELLATION_REASON_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'text-red-600'})
    )
    details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-red-500 focus:border-red-500 transition',
            'rows': 3,
            'placeholder': 'Please provide additional details about the cancellation...'
        }),
        required=False
    )


class TherapistScheduleForm(forms.ModelForm):
    """Form for therapists to set their availability schedule"""
    
    class Meta:
        model = TherapistSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_available', 'break_start', 'break_end']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'text-purple-600'
            elif isinstance(field.widget, forms.TimeInput):
                field.widget.attrs.update({
                    'type': 'time',
                    'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'
                })
            else:
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        break_start = cleaned_data.get('break_start')
        break_end = cleaned_data.get('break_end')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("End time must be after start time.")
        
        if break_start and break_end:
            if break_start >= break_end:
                raise ValidationError("Break end time must be after break start time.")
            
            if start_time and end_time:
                if break_start < start_time or break_end > end_time:
                    raise ValidationError("Break times must be within working hours.")
        
        return cleaned_data


class TherapistReviewForm(forms.ModelForm):
    """Form for patients to review therapists"""
    
    class Meta:
        model = TherapistReview
        fields = [
            'rating', 'communication_rating', 'professionalism_rating', 
            'effectiveness_rating', 'review_text', 'would_recommend', 'is_anonymous'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add star rating widgets
        rating_fields = ['rating', 'communication_rating', 'professionalism_rating', 'effectiveness_rating']
        for field_name in rating_fields:
            self.fields[field_name].widget = forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)]
            )
            self.fields[field_name].widget.attrs['class'] = 'star-rating text-yellow-500'
        
        # Style other fields
        self.fields['review_text'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'rows': 6,
            'placeholder': 'Share your experience with this therapist...'
        })
        
        self.fields['would_recommend'].widget.attrs['class'] = 'text-green-600'
        self.fields['is_anonymous'].widget.attrs['class'] = 'text-gray-600'


class AppointmentMessageForm(forms.ModelForm):
    """Form for sending messages related to appointments"""
    
    class Meta:
        model = AppointmentMessage
        fields = ['content', 'is_urgent', 'attachment']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['content'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'rows': 4,
            'placeholder': 'Type your message here...'
        })
        
        self.fields['is_urgent'].widget.attrs['class'] = 'text-red-600'
        self.fields['attachment'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'
        })


class PatientProfileForm(forms.ModelForm):
    """Form for patients to update their profile"""
    
    class Meta:
        model = PatientProfile
        fields = [
            'date_of_birth', 'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
            'insurance_provider', 'insurance_id', 'medical_conditions', 'medications',
            'preferred_therapist_gender', 'preferred_session_type', 'therapy_goals',
            'notifications_enabled', 'email_reminders', 'sms_reminders', 'profile_visibility'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_conditions': forms.Textarea(attrs={'rows': 3}),
            'medications': forms.Textarea(attrs={'rows': 3}),
            'therapy_goals': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style all form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'text-purple-600'
            elif isinstance(field.widget, (forms.Textarea, forms.TextInput, forms.EmailInput, forms.DateInput, forms.Select)):
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'


class TherapistSearchForm(forms.Form):
    """Advanced search form for finding therapists"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Search by name, specialization, or keywords...'
        })
    )
    
    specializations = forms.MultipleChoiceField(
        choices=TherapistProfile.SPECIALIZATION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'text-purple-600'})
    )
    
    languages = forms.MultipleChoiceField(
        choices=TherapistProfile.LANGUAGE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'text-purple-600'})
    )
    
    session_types = forms.MultipleChoiceField(
        choices=Appointment.SESSION_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'text-purple-600'})
    )
    
    max_rate = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Maximum hourly rate'
        })
    )
    
    min_rating = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition',
            'placeholder': 'Minimum rating',
            'step': '0.1'
        })
    )
    
    accepts_insurance = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'text-purple-600'})
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('rating', 'Highest Rated'),
            ('experience', 'Most Experienced'),
            ('rate_low', 'Lowest Rate'),
            ('rate_high', 'Highest Rate'),
            ('newest', 'Newest'),
            ('response_time', 'Fastest Response'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-gray-300 focus:ring-purple-500 focus:border-purple-500 transition'
        })
    )
