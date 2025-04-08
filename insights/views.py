from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from moodtracker.models import MoodEntry
from journal.models import JournalEntry
from chatbot.models import ChatMessage
from django.db.models import Count

@login_required
def insights_home(request):
    user = request.user

    # Mood Data Aggregated for Chart
    mood_data = (
        MoodEntry.objects.filter(user=user)
        .values('mood')
        .annotate(count=Count('mood'))
    )

    # Mood Count and Latest Mood
    mood_count = MoodEntry.objects.filter(user=user).count()
    latest_mood = (
        MoodEntry.objects.filter(user=user).order_by('-timestamp').first()
    )

    # Journal Entries
    journal_entries = JournalEntry.objects.filter(user=user).order_by('-date_created')
    journal_count = journal_entries.count()

    # Chat Messages and Bot Replies
    chat_messages = ChatMessage.objects.filter(user=user).order_by('-timestamp')
    user_msg_count = chat_messages.filter(sender='user').count()
    bot_msg_count = chat_messages.filter(sender='bot').count()

    context = {
        'mood_data': list(mood_data),
        'mood_count': mood_count,
        'latest_mood': latest_mood,
        'journal_entries': journal_entries,
        'journal_count': journal_count,
        'chat_messages': chat_messages,
        'user_msg_count': user_msg_count,
        'bot_msg_count': bot_msg_count,
    }

    return render(request, 'insights/insights_home.html', context)
