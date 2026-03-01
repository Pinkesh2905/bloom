from django.db import models
from django.conf import settings
from django.urls import reverse

class Tag(models.Model):
    """Model representing a tag for a journal entry."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class JournalEntry(models.Model):
    """Model representing a single journal entry."""

    class Mood(models.TextChoices):
        HAPPY = 'HAPPY', '😊 Happy'
        NEUTRAL = 'NEUTRAL', '😐 Neutral'
        SAD = 'SAD', '😔 Sad'
        EXCITED = 'EXCITED', '🤩 Excited'
        CALM = 'CALM', '😌 Calm'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journal_entries')
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    mood = models.CharField(max_length=10, choices=Mood.choices, default=Mood.NEUTRAL)
    mood_intensity = models.PositiveSmallIntegerField(default=5, help_text="Mood intensity from 1 to 10")
    sentiment_score = models.FloatField(default=0.0, help_text="AI calculated sentiment score (-1 to 1)")
    ai_reflection = models.TextField(blank=True, null=True, help_text="AI-generated reflection on the entry")
    image_attachment = models.ImageField(upload_to='journal_attachments/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='journal_entries')
    is_favorite = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this entry."""
        return reverse('journal_detail', args=[str(self.id)])
