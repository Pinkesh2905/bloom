from django import forms
from .models import MoodEntry

class MoodForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ['mood', 'note']
        widgets = {
            'mood': forms.RadioSelect(choices=MoodEntry.MOOD_CHOICES),
            'note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a short note...'}),
        }
