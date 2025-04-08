from django.shortcuts import render, redirect, get_object_or_404
from .models import Appointment, Therapist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AppointmentForm
from datetime import datetime, time as time_obj
from django.views.decorators.http import require_POST

def therapist_list(request):
    therapists = Therapist.objects.all()
    return render(request, 'therapists/therapist_list.html', {
        'therapists': therapists
    })

@login_required
def therapist_detail(request, pk):
    therapist = get_object_or_404(Therapist, pk=pk)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.therapist = therapist  # set therapist from URL
            appointment.save()
            messages.success(request, f"Appointment booked with {therapist.name}!")
            return redirect('user_appointments')
    else:
        form = AppointmentForm()

    return render(request, 'therapists/therapist_detail.html', {
        'therapist': therapist,
        'form': form
    })

@login_required
def user_appointments(request):
    now = datetime.now()
    appointments = Appointment.objects.filter(user=request.user)

    upcoming_appointments = []

    for appointment in appointments:
        # Combine appointment date and time into a datetime object
        appointment_datetime = datetime.combine(appointment.date, appointment.time)
        if appointment_datetime > now:
            upcoming_appointments.append(appointment)

    return render(request, 'therapists/user_appointments.html', {'appointments': upcoming_appointments})


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    appointment.delete()
    messages.success(request, "Your appointment has been cancelled.")
    return redirect('user_appointments')
