from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.conf import settings
import json
from datetime import datetime, timedelta, date
from .models import (
    TherapistProfile, Appointment, TherapistSchedule, TherapistReview, 
    PatientProfile, AppointmentMessage
)
from .forms import (
    TherapistSignUpForm, AdvancedAppointmentForm, AppointmentRescheduleForm,
    AppointmentCancelForm, TherapistScheduleForm, TherapistReviewForm,
    AppointmentMessageForm, PatientProfileForm, TherapistSearchForm,
    TherapistProfileUpdateForm
)
from .decorators import user_is_regular, user_is_therapist
from .utils import (
    send_appointment_notification, calculate_therapist_availability,
    get_therapist_analytics, validate_appointment_time, generate_ai_response,
    get_next_available_slot
)

# ===============================
# THERAPIST LIST AND SEARCH VIEWS
# ===============================

@login_required
@user_is_regular
def therapist_list(request):
    """Enhanced therapist list with advanced search and filtering"""
    form = TherapistSearchForm(request.GET or None)
    therapists = TherapistProfile.objects.filter(is_approved=True, is_verified=True)
    
    # Apply search filters
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        specializations = form.cleaned_data.get('specializations')
        languages = form.cleaned_data.get('languages')
        session_types = form.cleaned_data.get('session_types')
        max_rate = form.cleaned_data.get('max_rate')
        min_rating = form.cleaned_data.get('min_rating')
        accepts_insurance = form.cleaned_data.get('accepts_insurance')
        sort_by = form.cleaned_data.get('sort_by')
        
        # Text search
        if search_query:
            therapists = therapists.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(bio__icontains=search_query) |
                Q(specializations__icontains=search_query)
            )
        
        # Filter by specializations
        if specializations:
            for spec in specializations:
                therapists = therapists.filter(specializations__contains=[spec])
        
        # Filter by languages
        if languages:
            for lang in languages:
                therapists = therapists.filter(languages_spoken__contains=[lang])
        
        # Filter by session types
        if session_types:
            session_filter = Q()
            for session_type in session_types:
                if session_type == 'VIDEO':
                    session_filter |= Q(offers_video_sessions=True)
                elif session_type == 'CHAT':
                    session_filter |= Q(offers_chat_sessions=True)
                elif session_type == 'PHONE':
                    session_filter |= Q(offers_phone_sessions=True)
                elif session_type == 'IN_PERSON':
                    session_filter |= Q(offers_in_person=True)
            therapists = therapists.filter(session_filter)
        
        # Filter by rate and rating
        if max_rate:
            therapists = therapists.filter(hourly_rate__lte=max_rate)
        if min_rating:
            therapists = therapists.filter(rating__gte=min_rating)
        if accepts_insurance:
            therapists = therapists.filter(accepts_insurance=True)
        
        # Apply sorting
        if sort_by:
            sort_mapping = {
                'rating': '-rating',
                'experience': '-years_experience',
                'rate_low': 'hourly_rate',
                'rate_high': '-hourly_rate',
                'newest': '-created_at',
                'response_time': 'response_time_hours',
            }
            therapists = therapists.order_by(sort_mapping.get(sort_by, '-rating'))
    else:
        # Default sorting by rating
        therapists = therapists.order_by('-rating', '-total_reviews')
    
    # Pagination
    paginator = Paginator(therapists, 12)
    page_number = request.GET.get('page')
    therapists_page = paginator.get_page(page_number)
    
    # Get popular specializations for sidebar
    popular_specs = TherapistProfile.objects.filter(
        is_approved=True, is_verified=True
    ).values_list('specializations', flat=True)
    
    # Flatten and count specializations
    from collections import Counter
    all_specs = []
    for spec_list in popular_specs:
        all_specs.extend(spec_list)
    popular_specs = Counter(all_specs).most_common(8)
    
    context = {
        'therapists': therapists_page,
        'form': form,
        'popular_specializations': popular_specs,
        'total_count': therapists.count(),
        'has_search': any(request.GET.values())
    }
    
    return render(request, 'therapists/therapist_list.html', context)


@login_required
@user_is_regular
def therapist_detail(request, therapist_id):
    """Enhanced therapist detail view with reviews and availability"""
    therapist = get_object_or_404(
        TherapistProfile, 
        id=therapist_id, 
        is_approved=True, 
        is_verified=True
    )
    
    # Get therapist reviews
    reviews = TherapistReview.objects.filter(
        therapist=therapist, 
        is_public=True
    ).order_by('-created_at')[:10]
    
    # Calculate review statistics
    review_stats = TherapistReview.objects.filter(therapist=therapist).aggregate(
        avg_communication=Avg('communication_rating'),
        avg_professionalism=Avg('professionalism_rating'),
        avg_effectiveness=Avg('effectiveness_rating'),
        total_reviews=Count('id')
    )
    
    # Get next available appointment slot
    next_date, next_time = get_next_available_slot(therapist)
    
    # Check if user has had appointments with this therapist
    can_review = False
    if request.user.is_authenticated:
        completed_appointments = Appointment.objects.filter(
            patient=request.user,
            therapist=therapist,
            status='COMPLETED'
        ).exists()
        
        already_reviewed = TherapistReview.objects.filter(
            patient=request.user,
            therapist=therapist
        ).exists()
        
        can_review = completed_appointments and not already_reviewed
    
    context = {
        'therapist': therapist,
        'reviews': reviews,
        'review_stats': review_stats,
        'next_available_date': next_date,
        'next_available_time': next_time,
        'can_review': can_review,
        'session_types': therapist.get_available_session_types()
    }
    
    return render(request, 'therapists/therapist_detail.html', context)

# ===============================
# APPOINTMENT BOOKING VIEWS
# ===============================

@login_required
@user_is_regular
def book_appointment(request, therapist_id):
    """Enhanced appointment booking with availability checking"""
    therapist = get_object_or_404(TherapistProfile, id=therapist_id, is_approved=True)
    
    if request.method == 'POST':
        form = AdvancedAppointmentForm(therapist=therapist, data=request.POST)
        if form.is_valid():
            # Handle multiple preferred dates/times
            preferred_dates = form.cleaned_data['preferred_dates']
            preferred_times = form.cleaned_data['preferred_times']
            urgency_level = form.cleaned_data['urgency_level']
            
            # Find best available slot
            best_slot = None
            for preferred_date in preferred_dates:
                available_times = calculate_therapist_availability(therapist, preferred_date)
                for preferred_time_str in preferred_times:
                    preferred_time = datetime.strptime(preferred_time_str, '%H:%M').time()
                    if preferred_time in available_times:
                        best_slot = (preferred_date, preferred_time)
                        break
                if best_slot:
                    break
            
            if best_slot:
                # Create appointment
                appointment = Appointment.objects.create(
                    patient=request.user,
                    therapist=therapist,
                    date=best_slot[0],
                    time=best_slot[1],
                    session_type=form.cleaned_data['session_type'],
                    patient_notes=form.cleaned_data['patient_notes'],
                    cost=therapist.hourly_rate,
                    duration=therapist.session_duration
                )
                
                # Send notifications
                send_appointment_notification(appointment, 'booking')
                
                messages.success(
                    request, 
                    f'Successfully booked appointment with {therapist.full_name} for {best_slot[0]} at {best_slot[1]}!'
                )
                return redirect('therapists:booking_success', appointment_id=appointment.id)
            else:
                # No slots available, suggest alternatives
                next_date, next_time = get_next_available_slot(therapist)
                if next_date:
                    messages.warning(
                        request,
                        f'Your preferred times are not available. The next available slot is {next_date} at {next_time}.'
                    )
                else:
                    messages.error(
                        request,
                        'No available slots found. Please contact the therapist directly.'
                    )
    else:
        form = AdvancedAppointmentForm(therapist=therapist)
    
    # Get therapist's availability for next 30 days
    availability_data = {}
    for i in range(30):
        check_date = date.today() + timedelta(days=i)
        available_times = calculate_therapist_availability(therapist, check_date)
        if available_times:
            availability_data[check_date.isoformat()] = [
                time.strftime('%H:%M') for time in available_times
            ]
    
    context = {
        'form': form,
        'therapist': therapist,
        'availability_data': json.dumps(availability_data),
    }
    
    return render(request, 'therapists/book_appointment.html', context)


@login_required
def booking_success(request, appointment_id=None):
    """Enhanced booking success page with appointment details"""
    appointment = None
    if appointment_id:
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                patient=request.user
            )
        except Appointment.DoesNotExist:
            messages.error(request, "Appointment not found.")
            return redirect('therapists:therapist_list')
    
    context = {
        'appointment': appointment
    }
    return render(request, 'therapists/booking_success.html', context)


@login_required
def reschedule_appointment(request, appointment_id):
    """Reschedule an existing appointment"""
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id,
        patient=request.user,
        status__in=['PENDING', 'CONFIRMED']
    )
    
    if not appointment.can_be_rescheduled():
        messages.error(request, "This appointment cannot be rescheduled.")
        return redirect('profile')
    
    if request.method == 'POST':
        form = AppointmentRescheduleForm(request.POST)
        if form.is_valid():
            new_date = form.cleaned_data['new_date']
            new_time = form.cleaned_data['new_time']
            reason = form.cleaned_data['reason']
            
            # Validate new time slot
            is_valid, error_msg = validate_appointment_time(
                appointment.therapist, new_date, new_time
            )
            
            if is_valid:
                # Create new appointment
                new_appointment = Appointment.objects.create(
                    patient=appointment.patient,
                    therapist=appointment.therapist,
                    date=new_date,
                    time=new_time,
                    session_type=appointment.session_type,
                    patient_notes=appointment.patient_notes,
                    cost=appointment.cost,
                    duration=appointment.duration,
                    rescheduled_from=appointment
                )
                
                # Update old appointment
                appointment.status = 'RESCHEDULED'
                appointment.cancellation_details = reason
                appointment.save()
                
                send_appointment_notification(new_appointment, 'booking')
                messages.success(request, 'Appointment successfully rescheduled!')
                return redirect('therapists:booking_success', appointment_id=new_appointment.id)
            else:
                messages.error(request, error_msg)
    else:
        form = AppointmentRescheduleForm()
    
    # Get available slots
    availability_data = {}
    for i in range(30):
        check_date = date.today() + timedelta(days=i+1)
        available_times = calculate_therapist_availability(appointment.therapist, check_date)
        if available_times:
            availability_data[check_date.isoformat()] = [
                time.strftime('%H:%M') for time in available_times
            ]
    
    context = {
        'form': form,
        'appointment': appointment,
        'availability_data': json.dumps(availability_data)
    }
    
    return render(request, 'therapists/reschedule_appointment.html', context)


@login_required
def cancel_appointment(request, appointment_id):
    """Cancel an existing appointment"""
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,
        status__in=['PENDING', 'CONFIRMED']
    )
    
    if request.method == 'POST':
        form = AppointmentCancelForm(request.POST)
        if form.is_valid():
            appointment.status = 'CANCELLED_BY_PATIENT'
            appointment.cancellation_reason = form.cleaned_data['cancellation_reason']
            appointment.cancellation_details = form.cleaned_data['details']
            appointment.cancelled_at = timezone.now()
            appointment.cancelled_by = request.user
            appointment.save()
            
            messages.success(request, 'Appointment cancelled successfully.')
            return redirect('profile')
    else:
        form = AppointmentCancelForm()
    
    context = {
        'form': form,
        'appointment': appointment,
        'can_cancel': appointment.can_be_cancelled()
    }
    
    return render(request, 'therapists/cancel_appointment.html', context)

# ===============================
# THERAPIST DASHBOARD VIEWS
# ===============================

@login_required
@user_is_therapist
def therapist_dashboard(request):
    """Enhanced therapist dashboard with analytics and insights"""
    try:
        therapist = request.user.therapist_profile
    except TherapistProfile.DoesNotExist:
        raise PermissionDenied("You do not have access to this page.")
    
    # Get appointments
    upcoming_appointments = Appointment.objects.filter(
        therapist=therapist,
        date__gte=timezone.now().date(),
        status__in=['PENDING', 'CONFIRMED']
    ).order_by('date', 'time')[:10]
    
    today_appointments = Appointment.objects.filter(
        therapist=therapist,
        date=timezone.now().date(),
        status__in=['PENDING', 'CONFIRMED']
    ).order_by('time')
    
    # Get recent messages
    recent_messages = AppointmentMessage.objects.filter(
        appointment__therapist=therapist,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Get analytics
    analytics = get_therapist_analytics(therapist)
    
    # Get profile completion percentage
    profile_completion = therapist.calculate_profile_completeness()
    
    # Get pending reviews responses
    pending_reviews = TherapistReview.objects.filter(
        therapist=therapist,
        therapist_response='',
        review_text__isnull=False
    ).exclude(review_text='').count()
    
    context = {
        'therapist': therapist,
        'upcoming_appointments': upcoming_appointments,
        'today_appointments': today_appointments,
        'recent_messages': recent_messages,
        'analytics': analytics,
        'profile_completion': profile_completion,
        'pending_reviews': pending_reviews
    }
    
    return render(request, 'therapists/therapist_dashboard.html', context)


@login_required
@user_is_therapist
def therapist_appointments(request):
    """Detailed appointments view for therapists"""
    try:
        therapist = request.user.therapist_profile
    except TherapistProfile.DoesNotExist:
        raise PermissionDenied("You do not have access to this page.")
    
    # Filter appointments
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', 'all')
    
    appointments = Appointment.objects.filter(therapist=therapist)
    
    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)
    
    if date_filter == 'today':
        appointments = appointments.filter(date=timezone.now().date())
    elif date_filter == 'week':
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=7)
        appointments = appointments.filter(date__range=[start_date, end_date])
    elif date_filter == 'month':
        start_date = timezone.now().date().replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        appointments = appointments.filter(date__range=[start_date, end_date])
    
    appointments = appointments.order_by('-date', '-time')
    
    # Pagination
    paginator = Paginator(appointments, 20)
    page_number = request.GET.get('page')
    appointments_page = paginator.get_page(page_number)
    
    context = {
        'appointments': appointments_page,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': Appointment.STATUS_CHOICES
    }
    
    return render(request, 'therapists/therapist_appointments.html', context)


@login_required
@user_is_therapist
def update_therapist_profile(request):
    """Allow therapists to update their profile"""
    try:
        therapist = request.user.therapist_profile
    except TherapistProfile.DoesNotExist:
        raise PermissionDenied("You do not have access to this page.")
    
    if request.method == 'POST':
        form = TherapistProfileUpdateForm(request.POST, request.FILES, instance=therapist)
        if form.is_valid():
            updated_therapist = form.save()
            updated_therapist.calculate_profile_completeness()
            updated_therapist.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('therapists:therapist_dashboard')
    else:
        form = TherapistProfileUpdateForm(instance=therapist)
    
    context = {
        'form': form,
        'therapist': therapist
    }
    
    return render(request, 'therapists/update_profile.html', context)


@login_required
@user_is_therapist
def manage_schedule(request):
    """Allow therapists to manage their availability schedule"""
    try:
        therapist = request.user.therapist_profile
    except TherapistProfile.DoesNotExist:
        raise PermissionDenied("You do not have access to this page.")
    
    schedules = TherapistSchedule.objects.filter(therapist=therapist).order_by('day_of_week')
    
    if request.method == 'POST':
        form = TherapistScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.therapist = therapist
            schedule.save()
            messages.success(request, 'Schedule updated successfully!')
            return redirect('therapists:manage_schedule')
    else:
        form = TherapistScheduleForm()
    
    context = {
        'form': form,
        'schedules': schedules,
        'weekdays': TherapistSchedule.WEEKDAYS
    }
    
    return render(request, 'therapists/manage_schedule.html', context)

# ===============================
# MESSAGING AND COMMUNICATION VIEWS
# ===============================

@login_required
def appointment_messages(request, appointment_id):
    """View and send messages for a specific appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if request.user != appointment.patient and request.user != appointment.therapist.user:
        raise PermissionDenied("You don't have access to these messages.")
    
    # Mark messages as read
    AppointmentMessage.objects.filter(
        appointment=appointment,
        sender__ne=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    messages_list = AppointmentMessage.objects.filter(
        appointment=appointment
    ).order_by('created_at')
    
    if request.method == 'POST':
        form = AppointmentMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.appointment = appointment
            message.sender = request.user
            message.save()
            
            # Generate AI response if user is patient and therapist has AI enabled
            if (request.user == appointment.patient and 
                getattr(settings, 'ENABLE_AI_THERAPIST_RESPONSES', False)):
                ai_response = generate_ai_response(
                    message.content, 
                    appointment, 
                    'general'
                )
                if ai_response:
                    AppointmentMessage.objects.create(
                        appointment=appointment,
                        sender=appointment.therapist.user,
                        content=ai_response,
                        ai_generated=True,
                        ai_confidence=0.8
                    )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('therapists:appointment_messages', appointment_id=appointment.id)
    else:
        form = AppointmentMessageForm()
    
    context = {
        'appointment': appointment,
        'messages': messages_list,
        'form': form
    }
    
    return render(request, 'therapists/appointment_messages.html', context)

# ===============================
# REVIEW SYSTEM VIEWS
# ===============================

@login_required
def leave_review(request, appointment_id):
    """Allow patients to leave reviews for completed appointments"""
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,
        status='COMPLETED'
    )
    
    # Check if review already exists
    if TherapistReview.objects.filter(patient=request.user, appointment=appointment).exists():
        messages.info(request, 'You have already reviewed this therapist.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = TherapistReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.patient = request.user
            review.therapist = appointment.therapist
            review.appointment = appointment
            review.save()
            
            messages.success(request, 'Thank you for your review!')
            return redirect('profile')
    else:
        form = TherapistReviewForm()
    
    context = {
        'form': form,
        'appointment': appointment
    }
    
    return render(request, 'therapists/leave_review.html', context)


@login_required
@user_is_therapist
def respond_to_review(request, review_id):
    """Allow therapists to respond to reviews"""
    review = get_object_or_404(TherapistReview, id=review_id, therapist=request.user.therapist_profile)
    
    if request.method == 'POST':
        response_text = request.POST.get('response', '').strip()
        if response_text:
            review.therapist_response = response_text
            review.responded_at = timezone.now()
            review.save()
            
            messages.success(request, 'Response added successfully!')
            return redirect('therapists:therapist_dashboard')
        else:
            messages.error(request, 'Please enter a response.')
    
    context = {
        'review': review
    }
    
    return render(request, 'therapists/respond_to_review.html', context)

# ===============================
# API AND AJAX VIEWS
# ===============================

@login_required
def get_availability(request, therapist_id):
    """Get therapist availability for a specific date"""
    therapist = get_object_or_404(TherapistProfile, id=therapist_id)
    date_str = request.GET.get('date')
    
    try:
        requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        available_times = calculate_therapist_availability(therapist, requested_date)
        
        time_slots = [
            {
                'time': time.strftime('%H:%M'),
                'display': time.strftime('%I:%M %p')
            }
            for time in available_times
        ]
        
        return JsonResponse({
            'success': True,
            'slots': time_slots
        })
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid date format'
        })


@login_required
@require_http_methods(["POST"])
def confirm_appointment(request, appointment_id):
    """Allow therapists to confirm appointments"""
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        therapist__user=request.user,
        status='PENDING'
    )
    
    appointment.status = 'CONFIRMED'
    appointment.confirmed_at = timezone.now()
    appointment.save()
    
    send_appointment_notification(appointment, 'confirmation')
    
    return JsonResponse({
        'success': True,
        'message': 'Appointment confirmed successfully'
    })


def therapist_signup(request):
    """
    Handles therapist signup.
    - If GET, shows a new form.
    - If POST and valid, saves the form and redirects.
    - If POST and invalid, re-renders the form with errors and user data.
    """
    if request.method == 'POST':
        form = TherapistSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                'Your therapist application has been submitted successfully! '
                'We will review your credentials and notify you via email once approved.'
            )
            # You might want to log the user in directly here
            # from django.contrib.auth import login
            # login(request, user)
            return redirect('login') # Redirect to login page after successful signup
        else:
            # This block is the critical fix. It handles the invalid form submission.
            messages.error(
                request,
                'Please correct the errors below and try again.'
            )
            # The invalid form (with errors and user data) is passed back to the template
            context = {'form': form}
            return render(request, 'therapists/therapist_signup.html', context)
    else:
        # This handles the initial GET request
        form = TherapistSignUpForm()
    
    context = {'form': form}
    return render(request, 'therapists/therapist_signup.html', context)


class CustomLoginView(LoginView):
    """Enhanced login view with proper redirects"""
    template_name = 'therapists/login.html'
    
    def get_success_url(self):
        user = self.request.user
        
        # Check if user is an approved therapist
        if hasattr(user, 'therapist_profile') and user.therapist_profile.is_approved:
            return reverse_lazy('therapists:therapist_dashboard')
        else:
            # Regular user or non-approved therapist
            return reverse_lazy('profile')


# ===============================
# PATIENT PROFILE VIEWS
# ===============================

@login_required
@user_is_regular
def update_patient_profile(request):
    """Allow patients to update their profile"""
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = PatientProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile
    }
    
    return render(request, 'therapists/update_patient_profile.html', context)