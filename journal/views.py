from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from .models import JournalEntry, Tag
from .forms import JournalEntryForm
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta
import random

class JournalListView(LoginRequiredMixin, ListView):
    model = JournalEntry
    template_name = 'journal/journal_list.html'
    context_object_name = 'entries'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        queryset = JournalEntry.objects.filter(user=user).select_related('user').prefetch_related('tags')

        # Handle search query
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )

        # Handle tag filtering
        tag_filter = self.request.GET.get('tag')
        if tag_filter:
            queryset = queryset.filter(tags__name__iexact=tag_filter)

        return queryset.order_by('-date_created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_tags'] = Tag.objects.filter(journal_entries__user=self.request.user).distinct()
        context['search_query'] = self.request.GET.get('q', '')
        context['tag_filter'] = self.request.GET.get('tag', '')
        
        # Add mood distribution for sidebar
        user_entries = JournalEntry.objects.filter(user=self.request.user)
        context['mood_stats'] = user_entries.values('mood').annotate(count=Count('mood'))
        context['total_entries'] = user_entries.count()
        return context


class JournalDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = JournalEntry
    template_name = 'journal/journal_detail.html'

    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Map sentiment_score (-1 to 1) to percentage (0 to 100)
        score = self.object.sentiment_score
        context['sentiment_percentage'] = (score + 1) / 2 * 100
        return context


class JournalCreateView(LoginRequiredMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'journal/journal_form.html'
    success_url = reverse_lazy('journal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Simple Mock AI sentiment analysis
        content = form.cleaned_data.get('content', '').lower()
        positive_words = ['happy', 'great', 'good', 'excited', 'love', 'amazing', 'productive', 'calm']
        negative_words = ['sad', 'bad', 'angry', 'stressed', 'anxious', 'tired', 'worst', 'pain']
        
        pos_count = sum(1 for word in positive_words if word in content)
        neg_count = sum(1 for word in negative_words if word in content)
        
        sentiment = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        form.instance.sentiment_score = max(min(sentiment, 1.0), -1.0)
        
        # Mock AI reflection
        reflections = [
            "Your reflection shows deep self-awareness. It's helpful to acknowledge these patterns.",
            "I noticed your mood intensity is elevated. Remember to practice mindfulness during these peaks.",
            "This entry captures a significant emotional moment. How do you feel about this now?",
            "Your thoughts are evolving. This progress is a testament to your mental resilience.",
            "Take a moment to appreciate the clarity in your writing today."
        ]
        form.instance.ai_reflection = random.choice(reflections)
        
        response = super().form_valid(form)

        # Process the tags
        tags_string = form.cleaned_data.get('tags_input', '')
        if tags_string:
            tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name__iexact=tag_name, defaults={'name': tag_name})
                self.object.tags.add(tag)
        
        return response


class JournalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'journal/journal_form.html'
    success_url = reverse_lazy('journal_list')

    def form_valid(self, form):
        # Update sentiment on edit
        content = form.cleaned_data.get('content', '').lower()
        positive_words = ['happy', 'great', 'good', 'excited', 'love', 'amazing', 'productive', 'calm']
        negative_words = ['sad', 'bad', 'angry', 'stressed', 'anxious', 'tired', 'worst', 'pain']
        
        pos_count = sum(1 for word in positive_words if word in content)
        neg_count = sum(1 for word in negative_words if word in content)
        
        sentiment = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        form.instance.sentiment_score = max(min(sentiment, 1.0), -1.0)

        response = super().form_valid(form)

        # Process the tags
        tags_string = form.cleaned_data.get('tags_input', '')
        tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]

        self.object.tags.clear()
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name__iexact=tag_name, defaults={'name': tag_name})
            self.object.tags.add(tag)

        return response

    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.user


class JournalDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = JournalEntry
    template_name = 'journal/journal_confirm_delete.html'
    success_url = reverse_lazy('journal_list')

    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.user


class MoodAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'journal/mood_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Last 30 days data
        last_30_days = timezone.now() - timedelta(days=30)
        recent_entries = JournalEntry.objects.filter(user=user, date_created__gte=last_30_days).order_by('date_created')
        
        # Aggregate mood data
        mood_history = []
        for entry in recent_entries:
            mood_history.append({
                'date': entry.date_created.strftime('%Y-%m-%d'),
                'intensity': entry.mood_intensity,
                'sentiment': entry.sentiment_score,
                'mood': entry.mood
            })
            
        context['mood_history'] = mood_history
        context['avg_sentiment'] = recent_entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0
        context['mood_counts'] = recent_entries.values('mood').annotate(count=Count('mood'))
        
        return context

