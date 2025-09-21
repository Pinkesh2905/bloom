from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from .models import JournalEntry, Tag
from .forms import JournalEntryForm
from django.db.models import Q

class JournalListView(LoginRequiredMixin, ListView):
    model = JournalEntry
    template_name = 'journal/journal_list.html'
    context_object_name = 'entries'
    paginate_by = 10

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
        return context


class JournalDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = JournalEntry
    template_name = 'journal/journal_detail.html'

    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.user


class JournalCreateView(LoginRequiredMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'journal/journal_form.html'
    success_url = reverse_lazy('journal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        # super().form_valid() will save the object and set it as self.object
        response = super().form_valid(form)

        # Now that self.object is saved, process the tags from 'tags_input'
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
        # Let the parent class handle saving the main object's fields
        response = super().form_valid(form)

        # Process the tags from the 'tags_input' field
        tags_string = form.cleaned_data.get('tags_input', '')
        tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]

        # Clear existing tags and add the new set of tags. This is a simple
        # and effective way to handle updates.
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

