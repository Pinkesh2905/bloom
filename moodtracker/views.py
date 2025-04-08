from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MoodForm
from .models import MoodEntry

@login_required
def mood_tracker(request):
    if request.method == 'POST':
        form = MoodForm(request.POST)
        if form.is_valid():
            mood_entry = form.save(commit=False)
            mood_entry.user = request.user
            mood_entry.save()
            return redirect('mood_tracker')
    else:
        form = MoodForm()
    
    mood_history = MoodEntry.objects.filter(user=request.user).order_by('-timestamp')[:10]

    return render(request, 'moodtracker/mood_tracker.html', {
        'form': form,
        'mood_history': mood_history
    })
