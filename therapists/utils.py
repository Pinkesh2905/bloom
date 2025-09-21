from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q, Avg
from datetime import datetime, timedelta, date, time
import openai
import logging
import json
import re
from typing import List, Dict, Optional, Tuple
import calendar

logger = logging.getLogger(__name__)

def send_appointment_notification(appointment, notification_type='booking'):
    """
    Send comprehensive email notifications for appointment actions
    
    Args:
        appointment: Appointment instance
        notification_type: 'booking', 'confirmation', 'cancellation', 'reminder'
    """
    try:
        context = {
            'appointment': appointment,
            'therapist': appointment.therapist,
            'patient': appointment.patient,
            'site_name': 'Bloom Mental Wellness',
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@bloom.com'),
        }
        
        if notification_type == 'booking':
            # Notification to therapist
            therapist_subject = f"New Appointment Request - {appointment.patient.get_full_name()}"
            therapist_html_message = render_to_string('therapists/emails/therapist_booking_notification.html', context)
            therapist_text_message = render_to_string('therapists/emails/therapist_booking_notification.txt', context)
            
            send_html_email(
                subject=therapist_subject,
                html_content=therapist_html_message,
                text_content=therapist_text_message,
                to_email=[appointment.therapist.user.email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
            
            # Notification to patient
            patient_subject = f"Appointment Request Submitted - Dr. {appointment.therapist.full_name}"
            patient_html_message = render_to_string('therapists/emails/patient_booking_notification.html', context)
            patient_text_message = render_to_string('therapists/emails/patient_booking_notification.txt', context)
            
            send_html_email(
                subject=patient_subject,
                html_content=patient_html_message,
                text_content=patient_text_message,
                to_email=[appointment.patient.email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
            
        elif notification_type == 'confirmation':
            # Send confirmation to both parties
            confirmation_subject = f"Appointment Confirmed - {appointment.date.strftime('%B %d, %Y')}"
            
            # To patient
            patient_html = render_to_string('therapists/emails/appointment_confirmation.html', context)
            patient_text = render_to_string('therapists/emails/appointment_confirmation.txt', context)
            
            send_html_email(
                subject=confirmation_subject,
                html_content=patient_html,
                text_content=patient_text,
                to_email=[appointment.patient.email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
            
        elif notification_type == 'reminder':
            # Send appointment reminder
            reminder_subject = f"Appointment Reminder - Tomorrow at {appointment.time.strftime('%I:%M %p')}"
            context['is_reminder'] = True
            
            patient_html = render_to_string('therapists/emails/appointment_reminder.html', context)
            patient_text = render_to_string('therapists/emails/appointment_reminder.txt', context)
            
            send_html_email(
                subject=reminder_subject,
                html_content=patient_html,
                text_content=patient_text,
                to_email=[appointment.patient.email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
            
        logger.info(f"Appointment {notification_type} notification sent successfully for appointment {appointment.id}")
        
    except Exception as e:
        logger.error(f"Failed to send appointment {notification_type} notification: {e}")

def send_html_email(subject, html_content, text_content, to_email, from_email):
    """Send HTML email with text fallback"""
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_email
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        logger.error(f"Failed to send HTML email: {e}")
        # Fallback to simple text email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=to_email,
            fail_silently=False,
        )

def generate_ai_response(patient_message, appointment, context_type='initial'):
    """
    Generate AI response for therapist using OpenAI with enhanced context awareness
    
    Args:
        patient_message: The patient's message content
        appointment: Appointment instance for context
        context_type: 'initial', 'follow_up', 'crisis', 'general'
    """
    try:
        # Check if AI is enabled
        if not getattr(settings, 'ENABLE_AI_THERAPIST_RESPONSES', False):
            return None
            
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            logger.warning("OpenAI API key not configured")
            return None
        
        # Set OpenAI API key
        openai.api_key = api_key
        
        # Build context-aware prompt based on appointment history and type
        therapist_specializations = ", ".join(appointment.therapist.specializations)
        appointment_history = get_appointment_context(appointment)
        
        # Crisis detection
        crisis_keywords = ['suicide', 'kill myself', 'end it all', 'hurt myself', 'emergency', 'crisis']
        is_crisis = any(keyword in patient_message.lower() for keyword in crisis_keywords)
        
        if is_crisis:
            # Return immediate crisis response - do not use AI for crisis situations
            return generate_crisis_response()
        
        # Build comprehensive context
        system_prompt = f"""
        You are an AI assistant helping a licensed therapist ({appointment.therapist.full_name}) respond to patient messages.
        
        Therapist specializations: {therapist_specializations}
        Appointment context: {appointment_history}
        
        Guidelines:
        1. Maintain professional therapeutic tone
        2. Show empathy and active listening
        3. Avoid diagnosis or medical advice
        4. Encourage face-to-face discussion for complex issues
        5. Keep responses supportive but brief (2-3 sentences max)
        6. Reference the upcoming/recent session when appropriate
        7. Use person-first language
        8. Maintain appropriate boundaries
        """
        
        user_prompt = f"""
        Patient's message: "{patient_message}"
        Appointment type: {appointment.get_appointment_type_display()}
        Session context: {context_type}
        
        Generate a professional, empathetic response that acknowledges their concern and provides supportive guidance while maintaining therapeutic boundaries.
        """
        
        response = openai.ChatCompletion.create(
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.7,
            presence_penalty=0.3,
            frequency_penalty=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Add disclaimer
        ai_response += "\n\n(This is a preliminary AI-assisted response. We'll discuss this further in our session.)"
        
        logger.info(f"AI response generated successfully for appointment {appointment.id}")
        return ai_response
        
    except Exception as e:
        logger.error(f"AI response generation failed: {e}")
        return generate_fallback_response(patient_message)

def generate_crisis_response():
    """Generate immediate crisis response without AI"""
    return """
    Thank you for reaching out. I'm concerned about your wellbeing and want you to know that help is available immediately.
    
    If you're having thoughts of harming yourself, please:
    • Call 988 (Suicide & Crisis Lifeline) - available 24/7
    • Go to your nearest emergency room
    • Call 911
    
    I'll follow up with you shortly, but please prioritize your immediate safety. You matter, and there are people who want to help.
    """

def generate_fallback_response(patient_message):
    """Generate fallback response when AI is unavailable"""
    return f"""
    Thank you for sharing your thoughts with me. I've received your message and I appreciate you taking the time to communicate your concerns.
    
    I'll review what you've shared and we can discuss this further during our upcoming session. In the meantime, please don't hesitate to reach out if you need immediate support.
    
    Looking forward to our conversation.
    """

def get_appointment_context(appointment):
    """Get relevant context from previous appointments"""
    try:
        from .models import Appointment, AppointmentMessage
        
        # Get recent appointments with this patient
        recent_appointments = Appointment.objects.filter(
            therapist=appointment.therapist,
            patient=appointment.patient,
            status='completed'
        ).order_by('-date')[:3]
        
        context = f"Patient: {appointment.patient.get_full_name()}, "
        
        if recent_appointments.exists():
            context += f"Previous sessions: {recent_appointments.count()}, "
            # Get themes from recent session summaries
            recent_themes = []
            for apt in recent_appointments:
                if apt.session_summary:
                    recent_themes.append(apt.session_summary[:100])
            
            if recent_themes:
                context += f"Recent themes: {'; '.join(recent_themes)}"
        else:
            context += "New patient, first session"
            
        return context
        
    except Exception as e:
        logger.error(f"Failed to get appointment context: {e}")
        return "Standard therapeutic context"

def calculate_therapist_availability(therapist, date_requested):
    """
    Calculate available time slots for a therapist on a given date
    
    Returns list of available time slots
    """
    try:
        from .models import TherapistSchedule, Appointment
        
        day_of_week = date_requested.weekday()
        
        # Get therapist's schedule for this day
        schedules = TherapistSchedule.objects.filter(
            therapist=therapist,
            day_of_week=day_of_week,
            is_available=True
        )
        
        if not schedules.exists():
            return []
        
        # Get existing appointments for that date
        existing_appointments = Appointment.objects.filter(
            therapist=therapist,
            date=date_requested,
            status__in=['confirmed', 'pending']
        ).values_list('time', flat=True)
        
        available_slots = []
        
        for schedule in schedules:
            # Generate time slots (assuming 1-hour sessions)
            current_time = datetime.combine(date_requested, schedule.start_time)
            end_time = datetime.combine(date_requested, schedule.end_time)
            
            while current_time < end_time:
                slot_time = current_time.time()
                
                # Check if slot is not already booked
                if slot_time not in existing_appointments:
                    # Don't show past time slots for today
                    if date_requested == date.today():
                        now = datetime.now().time()
                        if slot_time > now:
                            available_slots.append(slot_time)
                    else:
                        available_slots.append(slot_time)
                
                current_time += timedelta(hours=1)
        
        return sorted(available_slots)
        
    except Exception as e:
        logger.error(f"Error calculating availability: {e}")
        return []

def get_therapist_analytics(therapist, days=30):
    """
    Get comprehensive analytics for therapist dashboard
    
    Returns dictionary with various metrics
    """
    try:
        from .models import Appointment, TherapistReview
        from django.db.models import Count, Avg
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Basic appointment metrics
        total_appointments = Appointment.objects.filter(
            therapist=therapist,
            date__gte=start_date,
            date__lte=end_date
        ).count()
        
        completed_appointments = Appointment.objects.filter(
            therapist=therapist,
            date__gte=start_date,
            date__lte=end_date,
            status='completed'
        ).count()
        
        pending_appointments = Appointment.objects.filter(
            therapist=therapist,
            status='pending'
        ).count()
        
        # Appointment status breakdown
        status_breakdown = Appointment.objects.filter(
            therapist=therapist,
            date__gte=start_date,
            date__lte=end_date
        ).values('status').annotate(count=Count('status'))
        
        # Weekly appointment trend
        weekly_data = []
        for week in range(4):
            week_start = end_date - timedelta(weeks=week+1)
            week_end = end_date - timedelta(weeks=week)
            week_count = Appointment.objects.filter(
                therapist=therapist,
                date__gte=week_start,
                date__lt=week_end,
                status='completed'
            ).count()
            weekly_data.append({
                'week': f"Week {4-week}",
                'appointments': week_count
            })
        
        # Patient retention (returning patients)
        unique_patients = Appointment.objects.filter(
            therapist=therapist,
            date__gte=start_date,
            date__lte=end_date
        ).values('patient').distinct().count()
        
        returning_patients = Appointment.objects.filter(
            therapist=therapist,
            date__gte=start_date,
            date__lte=end_date
        ).values('patient').annotate(
            appointment_count=Count('id')
        ).filter(appointment_count__gt=1).count()
        
        # Recent reviews
        recent_reviews = TherapistReview.objects.filter(
            therapist=therapist
        ).order_by('-created_at')[:5]
        
        # Average session duration (if tracked)
        avg_duration = Appointment.objects.filter(
            therapist=therapist,
            status='completed'
        ).aggregate(avg_duration=Avg('duration'))['avg_duration'] or 60
        
        return {
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'pending_appointments': pending_appointments,
            'status_breakdown': list(status_breakdown),
            'weekly_trend': weekly_data,
            'unique_patients': unique_patients,
            'returning_patients': returning_patients,
            'retention_rate': round((returning_patients / unique_patients * 100) if unique_patients > 0 else 0, 1),
            'recent_reviews': recent_reviews,
            'avg_duration': round(avg_duration),
            'rating': therapist.rating,
            'total_reviews': therapist.total_reviews
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return {}

def validate_appointment_time(therapist, appointment_date, appointment_time):
    """
    Validate if appointment time is available and within business hours
    
    Returns (is_valid, error_message)
    """
    try:
        from .models import TherapistSchedule, Appointment
        
        # Check if date is in the past
        if appointment_date < date.today():
            return False, "Cannot book appointments in the past"
        
        # Check if it's today and time has passed
        if appointment_date == date.today() and appointment_time <= datetime.now().time():
            return False, "Cannot book appointments in the past"
        
        # Check therapist's schedule
        day_of_week = appointment_date.weekday()
        schedule = TherapistSchedule.objects.filter(
            therapist=therapist,
            day_of_week=day_of_week,
            is_available=True,
            start_time__lte=appointment_time,
            end_time__gt=appointment_time
        ).first()
        
        if not schedule:
            return False, "Therapist is not available at this time"
        
        # Check for existing appointments
        existing = Appointment.objects.filter(
            therapist=therapist,
            date=appointment_date,
            time=appointment_time,
            status__in=['pending', 'confirmed']
        ).exists()
        
        if existing:
            return False, "This time slot is already booked"
        
        return True, "Time slot is available"
        
    except Exception as e:
        logger.error(f"Error validating appointment time: {e}")
        return False, "Error validating appointment time"

def send_appointment_reminders():
    """
    Send reminders for appointments happening tomorrow
    This would typically be run as a daily cron job
    """
    try:
        from .models import Appointment
        
        tomorrow = date.today() + timedelta(days=1)
        upcoming_appointments = Appointment.objects.filter(
            date=tomorrow,
            status='confirmed'
        )
        
        sent_count = 0
        for appointment in upcoming_appointments:
            send_appointment_notification(appointment, 'reminder')
            sent_count += 1
        
        logger.info(f"Sent {sent_count} appointment reminders for {tomorrow}")
        return sent_count
        
    except Exception as e:
        logger.error(f"Error sending appointment reminders: {e}")
        return 0

def update_therapist_rating(therapist):
    """Update therapist's average rating and review count"""
    try:
        from .models import TherapistReview
        
        reviews = TherapistReview.objects.filter(therapist=therapist)
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        
        therapist.rating = round(avg_rating, 2) if avg_rating else 0.00
        therapist.total_reviews = reviews.count()
        therapist.save(update_fields=['rating', 'total_reviews'])
        
        logger.info(f"Updated rating for {therapist}: {therapist.rating} ({therapist.total_reviews} reviews)")
        
    except Exception as e:
        logger.error(f"Error updating therapist rating: {e}")

def generate_appointment_summary(appointment):
    """Generate a summary for completed appointments using AI"""
    try:
        if not appointment.therapist_notes:
            return "No session notes provided."
        
        # Use AI to generate a concise summary if enabled
        if getattr(settings, 'ENABLE_AI_THERAPIST_RESPONSES', False):
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if api_key:
                openai.api_key = api_key
                
                response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=[
                        {
                            "role": "system", 
                            "content": "Generate a concise, professional summary of a therapy session based on the therapist's notes. Keep it confidential and therapeutic."
                        },
                        {
                            "role": "user", 
                            "content": f"Session notes: {appointment.therapist_notes}"
                        }
                    ],
                    max_tokens=100,
                    temperature=0.5
                )
                
                return response.choices[0].message.content.strip()
        
        # Fallback: simple truncation
        return appointment.therapist_notes[:200] + "..." if len(appointment.therapist_notes) > 200 else appointment.therapist_notes
        
    except Exception as e:
        logger.error(f"Error generating appointment summary: {e}")
        return "Summary generation failed."

def get_popular_specializations():
    """Get list of most popular specializations for analytics"""
    try:
        from .models import TherapistProfile
        from collections import Counter
        
        all_specializations = []
        for profile in TherapistProfile.objects.filter(is_verified=True):
            all_specializations.extend(profile.specializations)
        
        popular = Counter(all_specializations).most_common(10)
        return [{'name': name.replace('_', ' ').title(), 'count': count} for name, count in popular]
        
    except Exception as e:
        logger.error(f"Error getting popular specializations: {e}")
        return []

def format_time_slot(time_obj):
    """Format time object for display"""
    return time_obj.strftime("%I:%M %p")

def get_next_available_slot(therapist, preferred_date=None):
    """Find the next available appointment slot for a therapist"""
    try:
        from .models import TherapistSchedule, Appointment
        
        if not preferred_date:
            preferred_date = date.today() + timedelta(days=1)
        
        # Look up to 30 days ahead
        for days_ahead in range(30):
            check_date = preferred_date + timedelta(days=days_ahead)
            available_slots = calculate_therapist_availability(therapist, check_date)
            
            if available_slots:
                return check_date, available_slots[0]
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error finding next available slot: {e}")
        return None, None