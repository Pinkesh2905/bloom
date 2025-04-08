from django.db import models
from django.contrib.auth.models import User

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        ('happy', '😊 Happy'),
        ('sad', '😢 Sad'),
        ('angry', '😠 Angry'),
        ('anxious', '😰 Anxious'),
        ('excited', '🤩 Excited'),
        ('neutral', '😐 Neutral'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    note = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_mood_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
