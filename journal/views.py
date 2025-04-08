from django.shortcuts import render, redirect, get_object_or_404
from .models import JournalEntry
from .forms import JournalEntryForm
from django.contrib.auth.decorators import login_required

@login_required
def journal_list(request):
    entries = JournalEntry.objects.filter(user=request.user).order_by('-date_created')
    return render(request, 'journal/journal_list.html', {'entries': entries})

@login_required
def journal_create(request):
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.user = request.user
            journal.save()
            return redirect('journal_list')
    else:
        form = JournalEntryForm()
    return render(request, 'journal/journal_form.html', {'form': form})

@login_required
def journal_edit(request, pk):
    journal = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JournalEntryForm(request.POST, instance=journal)
        if form.is_valid():
            form.save()
            return redirect('journal_list')
    else:
        form = JournalEntryForm(instance=journal)
    return render(request, 'journal/journal_form.html', {'form': form})

@login_required
def journal_delete(request, pk):
    journal = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        journal.delete()
        return redirect('journal_list')
    return render(request, 'journal/journal_confirm_delete.html', {'journal': journal})
