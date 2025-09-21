from django import forms
from .models import JournalEntry, Tag

class JournalEntryForm(forms.ModelForm):
    # Field to capture the comma-separated tags as a string.
    # Renamed to 'tags_input' to avoid conflict with the model's 'tags' field.
    tags_input = forms.CharField(
        required=False,
        label="Tags", # This is the display label for the user
        help_text="Enter comma-separated tags.",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., travel, thoughts, work'})
    )

    class Meta:
        model = JournalEntry
        # The actual 'tags' ManyToManyField is excluded from the form's direct control.
        # It will be handled manually in the view.
        fields = ['title', 'content', 'mood', 'is_favorite']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing instance, populate the 'tags_input' string field
        # from the instance's related tags.
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(t.name for t in self.instance.tags.all())

