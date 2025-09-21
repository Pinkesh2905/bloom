from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from functools import wraps
import json

def user_is_therapist(function):
    """
    Enhanced decorator to check if the user is an approved therapist.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access this page.")
            return redirect('login')
        
        if hasattr(request.user, 'therapist_profile'):
            therapist = request.user.therapist_profile
            if therapist.is_approved and therapist.is_verified:
                return function(request, *args, **kwargs)
            elif not therapist.is_verified:
                messages.warning(request, "Please verify your email address to access the therapist dashboard.")
                return redirect('verify_email')
            elif not therapist.is_approved:
                messages.info(request, "Your therapist application is still under review. We'll notify you once it's approved.")
                return redirect('application_pending')
        else:
            messages.error(request, "You don't have permission to access this page. Are you a registered therapist?")
            return redirect('therapists:therapist_signup')
    
    return wrap


def user_is_regular(function):
    """
    Enhanced decorator to check if the user is a regular user (not a therapist accessing patient pages).
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access this page.")
            return redirect('login')
        
        # Check if user is an approved therapist trying to access patient pages
        if hasattr(request.user, 'therapist_profile'):
            therapist = request.user.therapist_profile
            if therapist.is_approved and therapist.is_verified:
                messages.info(request, "Therapists should use the therapist dashboard.")
                return redirect('therapists:therapist_dashboard')
        
        return function(request, *args, **kwargs)
    
    return wrap


def therapist_profile_required(function):
    """
    Decorator to ensure therapist has completed their profile.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not hasattr(request.user, 'therapist_profile'):
            raise PermissionDenied("Therapist profile required.")
        
        therapist = request.user.therapist_profile
        if not therapist.profile_complete:
            messages.warning(request, "Please complete your profile to access all features.")
            return redirect('therapists:update_therapist_profile')
        
        return function(request, *args, **kwargs)
    
    return wrap


def ajax_required(function):
    """
    Decorator to ensure request is made via AJAX.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'This endpoint requires AJAX request.'
            }, status=400)
        
        return function(request, *args, **kwargs)
    
    return wrap


def appointment_access_required(function):
    """
    Decorator to check if user has access to a specific appointment.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        from .models import Appointment
        appointment_id = kwargs.get('appointment_id')
        
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            messages.error(request, "Appointment not found.")
            return redirect('profile')
        
        # Check if user is either the patient or the therapist
        is_patient = request.user == appointment.patient
        is_therapist = (hasattr(request.user, 'therapist_profile') and 
                       request.user.therapist_profile == appointment.therapist)
        
        if not (is_patient or is_therapist):
            raise PermissionDenied("You don't have access to this appointment.")
        
        return function(request, *args, **kwargs)
    
    return wrap


def rate_limit(max_requests=60, window=3600):
    """
    Simple rate limiting decorator.
    """
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            from django.core.cache import cache
            import time
            
            # Create a unique key for this user and endpoint
            cache_key = f"rate_limit_{request.user.id}_{request.path}"
            
            # Get current request count and timestamp
            current_time = int(time.time())
            requests_data = cache.get(cache_key, {'count': 0, 'start_time': current_time})
            
            # Reset counter if window has passed
            if current_time - requests_data['start_time'] > window:
                requests_data = {'count': 1, 'start_time': current_time}
            else:
                requests_data['count'] += 1
            
            # Check if limit exceeded
            if requests_data['count'] > max_requests:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Rate limit exceeded. Please try again later.'
                    }, status=429)
                else:
                    messages.error(request, "Too many requests. Please try again later.")
                    return redirect('profile')
            
            # Update cache
            cache.set(cache_key, requests_data, window)
            
            return function(request, *args, **kwargs)
        
        return wrap
    return decorator


def verified_therapist_required(function):
    """
    Decorator for actions that require a fully verified therapist.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not hasattr(request.user, 'therapist_profile'):
            raise PermissionDenied("Therapist profile required.")
        
        therapist = request.user.therapist_profile
        
        if not therapist.is_verified:
            messages.warning(request, "Please verify your email address first.")
            return redirect('verify_email')
        
        if not therapist.license_verified:
            messages.warning(request, "Your professional license is still being verified.")
            return redirect('license_verification_pending')
        
        if not therapist.is_approved:
            messages.info(request, "Your application is still under review.")
            return redirect('application_pending')
        
        return function(request, *args, **kwargs)
    
    return wrap


def patient_profile_required(function):
    """
    Decorator to ensure patient has a complete profile for certain actions.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        from .models import PatientProfile
        
        try:
            profile = request.user.patient_profile
        except PatientProfile.DoesNotExist:
            profile = PatientProfile.objects.create(user=request.user)
        
        # Check if profile has minimum required information
        required_fields = [profile.phone_number, profile.emergency_contact_name, profile.emergency_contact_phone]
        if not all(required_fields):
            messages.warning(request, "Please complete your profile before booking appointments.")
            return redirect('therapists:update_patient_profile')
        
        return function(request, *args, **kwargs)
    
    return wrap


def appointment_status_required(allowed_statuses):
    """
    Decorator to check if appointment has specific status.
    """
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            from .models import Appointment
            appointment_id = kwargs.get('appointment_id')
            
            try:
                appointment = Appointment.objects.get(id=appointment_id)
            except Appointment.DoesNotExist:
                messages.error(request, "Appointment not found.")
                return redirect('profile')
            
            if appointment.status not in allowed_statuses:
                messages.error(request, f"This action is not available for appointments with status: {appointment.get_status_display()}")
                return redirect('profile')
            
            return function(request, *args, **kwargs)
        
        return wrap
    return decorator


def subscription_required(subscription_type='basic'):
    """
    Decorator for features that require specific subscription levels.
    (This would be useful if you implement a subscription system)
    """
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            # This is a placeholder for future subscription functionality
            # You can implement subscription checking logic here
            
            return function(request, *args, **kwargs)
        
        return wrap
    return decorator