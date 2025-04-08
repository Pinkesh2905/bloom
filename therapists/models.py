from django.db import models
from django.contrib.auth.models import User

class Therapist(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(help_text="Years of experience", default=0)  # Added field
    bio = models.TextField()
    image = models.ImageField(upload_to='therapists/', blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    therapist = models.ForeignKey(Therapist, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField()

    def __str__(self):
        return f"{self.user.username} with {self.therapist.name} on {self.date}"

class Tip(models.Model):
    therapist = models.ForeignKey(Therapist, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
