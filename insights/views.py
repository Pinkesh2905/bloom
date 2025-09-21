import re
from collections import Counter
from datetime import timedelta
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.utils import timezone

# Correctly import models from your existing apps
from journal.models import JournalEntry
from chatbot.models import ChatMessage, MoodEntry


# A list of common English "stop words" to exclude from the word cloud.
# You can expand this list for more accurate results.
STOP_WORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "did", "do", "does", "doing", "don", 
    "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", 
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", 
    "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", 
    "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", 
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", 
    "she", "should", "so", "some", "such", "t", "than", "that", "the", "their", "theirs", 
    "them", "themselves", "then", "there", "these", "they", "this", "those", "through", 
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", 
    "where", "which", "while", "who", "whom", "why", "will", "with", "you", "your", 
    "yours", "yourself", "yourselves", "im", "ive", "its"
])


class InsightsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'insights/insights_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # --- 1. Date Filtering Logic ---
        period = self.request.GET.get('period', 'month') # Default to 'month'
        today = timezone.now().date()
        start_date = today

        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif period == 'month':
            start_date = today.replace(day=1)
        elif period == 'year':
            start_date = today.replace(day=1, month=1)
        elif period == 'all':
            # Effectively no start date, will fetch all records
            start_date = None 
        
        # Base querysets for filtering
        mood_queryset = MoodEntry.objects.filter(user=user)
        journal_queryset = JournalEntry.objects.filter(user=user)
        chat_queryset = ChatMessage.objects.filter(user=user)

        if start_date:
            # Corrected field names for filtering
            mood_queryset = mood_queryset.filter(date__gte=start_date)
            journal_queryset = journal_queryset.filter(date_created__gte=start_date)
            chat_queryset = chat_queryset.filter(timestamp__gte=start_date)

        # --- 2. Data for KPI Cards ---
        context['mood_count'] = mood_queryset.count()
        context['journal_count'] = journal_queryset.count()
        context['user_msg_count'] = chat_queryset.filter(sender='user').count()
        context['bot_msg_count'] = chat_queryset.filter(sender='bot').count()

        # --- 3. Mood Distribution (Pie Chart) ---
        mood_distribution = list(
            mood_queryset.values('mood')
            .annotate(count=Count('mood'))
            .order_by('-count')
        )
        context['mood_distribution_data'] = mood_distribution

        # --- 4. Journaling Frequency (Bar Chart) ---
        journal_frequency = (
            journal_queryset
            .annotate(day=TruncDay('date_created'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        context['journal_frequency_data'] = list(journal_frequency)

        # --- 5. Word Cloud from Journal Entries (with font size calculation) ---
        all_journal_text = ' '.join(journal_queryset.values_list('content', flat=True))
        words = re.findall(r'\b\w+\b', all_journal_text.lower())
        filtered_words = [word for word in words if word not in STOP_WORDS and not word.isdigit()]
        word_counts = Counter(filtered_words).most_common(30)
        
        # Prepare data for template, including calculated font size
        max_count = word_counts[0][1] if word_counts else 1
        word_cloud_list = []
        for word, count in word_counts:
            # Scale font size between a min and max value for better visuals
            min_font_size = 0.8
            max_font_size = 2.2
            # Normalize count (0 to 1) relative to the most frequent word
            normalized_count = count / max_count
            font_size = min_font_size + (normalized_count * (max_font_size - min_font_size))
            
            word_cloud_list.append({
                'word': word,
                'font_size': round(font_size, 2)
            })
        context['word_cloud_data'] = word_cloud_list
        
        # --- 6. Recent Activity ---
        # Corrected ordering field for MoodEntry
        context['latest_mood'] = MoodEntry.objects.filter(user=user).order_by('-date').first()
        context['latest_journal'] = JournalEntry.objects.filter(user=user).order_by('-date_created').first()
        context['latest_chat'] = ChatMessage.objects.filter(user=user, sender='user').order_by('-timestamp').first()

        context['selected_period'] = period
        context['view_title'] = "Wellness Insights"
        return context

