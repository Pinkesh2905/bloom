from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import json
import uuid

class UserProfile(models.Model):
    """Extended user profile for mental wellness tracking"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_name = models.CharField(max_length=50, default="Friend")
    mood_tracking_enabled = models.BooleanField(default=True)
    daily_check_in_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)  # Track longest streak ever
    total_conversations = models.IntegerField(default=0)
    total_messages_sent = models.IntegerField(default=0)  # Track individual messages
    favorite_activities = models.JSONField(default=list, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    bot_personality = models.ForeignKey('BotPersonality', null=True, blank=True, on_delete=models.SET_NULL)
    last_check_in_date = models.DateField(null=True, blank=True)  # Track last check-in for streak calculation
    wellness_score = models.FloatField(default=0.0)  # Overall wellness score
    privacy_settings = models.JSONField(default=dict, blank=True)  # Store privacy preferences
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_streak(self):
        """Update check-in streak based on last check-in date"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if not self.last_check_in_date:
            # First check-in ever
            self.daily_check_in_streak = 1
        elif self.last_check_in_date == yesterday:
            # Consecutive day
            self.daily_check_in_streak += 1
        elif self.last_check_in_date == today:
            # Already checked in today, no change
            return
        else:
            # Streak broken
            self.daily_check_in_streak = 1
        
        # Update longest streak
        if self.daily_check_in_streak > self.longest_streak:
            self.longest_streak = self.daily_check_in_streak
            
        self.last_check_in_date = today
        self.save()
    
    def reset_streak(self):
        self.daily_check_in_streak = 0
        self.save()
    
    def calculate_wellness_score(self):
        """Calculate overall wellness score based on recent mood entries"""
        recent_moods = MoodEntry.objects.filter(
            user=self.user, 
            date__gte=date.today() - timedelta(days=30)
        )
        
        if not recent_moods.exists():
            return 0.0
            
        mood_values = {
            'terrible': 1, 'bad': 2, 'okay': 3, 
            'good': 4, 'great': 5, 'amazing': 6
        }
        
        total_score = sum(mood_values.get(mood.mood, 3) for mood in recent_moods)
        max_possible = len(recent_moods) * 6
        
        self.wellness_score = (total_score / max_possible) * 100 if max_possible > 0 else 0.0
        self.save()
        return self.wellness_score

class MoodEntry(models.Model):
    """Track user's daily mood entries with enhanced analytics"""
    MOOD_CHOICES = [
        ('terrible', 'Terrible'), ('bad', 'Bad'), ('okay', 'Okay'),
        ('good', 'Good'), ('great', 'Great'), ('amazing', 'Amazing'),
    ]
    
    ENERGY_CHOICES = [(i, str(i)) for i in range(1, 6)]
    STRESS_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_mood_entries')
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    energy_level = models.IntegerField(choices=ENERGY_CHOICES, default=3)
    stress_level = models.IntegerField(choices=STRESS_CHOICES, default=3)
    sleep_hours = models.FloatField(null=True, blank=True, help_text="Hours of sleep last night")
    physical_activity = models.BooleanField(default=False, help_text="Did physical activity today")
    social_interaction = models.BooleanField(default=False, help_text="Had meaningful social interaction")
    gratitude_note = models.TextField(blank=True, null=True, max_length=500)
    mood_triggers = models.JSONField(default=list, blank=True, help_text="What triggered this mood")
    date = models.DateField(default=date.today)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.mood} on {self.date}"
    
    def get_mood_score(self):
        """Return numerical score for mood (1-6)"""
        mood_values = {
            'terrible': 1, 'bad': 2, 'okay': 3, 
            'good': 4, 'great': 5, 'amazing': 6
        }
        return mood_values.get(self.mood, 3)

class ConversationSession(models.Model):
    """Track conversation sessions with enhanced analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_sessions')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=100, blank=True)  # Session title based on first message
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    message_count = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)  # Average bot response time
    sentiment_score = models.FloatField(default=0.0)  # Overall conversation sentiment
    topics_discussed = models.JSONField(default=list, blank=True)
    crisis_flags = models.IntegerField(default=0)  # Number of crisis indicators detected
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"
    
    def update_title(self):
        """Auto-generate title based on first user message"""
        if not self.title:
            first_message = self.chatmessage_set.filter(sender='user').first()
            if first_message:
                words = first_message.message.split()[:6]
                self.title = ' '.join(words) + ('...' if len(first_message.message.split()) > 6 else '')
                self.save()

class ChatMessage(models.Model):
    """Enhanced chat messages with NLP features"""
    SENDER_CHOICES = [('user', 'User'), ('bot', 'Bot')]
    MESSAGE_TYPES = [
        ('general', 'General Chat'), ('mood_check', 'Mood Check-in'),
        ('breathing', 'Breathing Exercise'), ('motivation', 'Motivation'),
        ('joke', 'Humor'), ('gratitude', 'Gratitude'),
        ('therapy', 'Mini Therapy'), ('crisis', 'Crisis Support'),
        ('goal_checkin', 'Goal Check-in'), ('reflection', 'Reflection'),
        ('coping_strategy', 'Coping Strategy'), ('mindfulness', 'Mindfulness'),
    ]
    
    SENTIMENT_CHOICES = [
        ('very_negative', 'Very Negative'), ('negative', 'Negative'),
        ('neutral', 'Neutral'), ('positive', 'Positive'),
        ('very_positive', 'Very Positive')
    ]
    
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='general')
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='neutral')
    confidence_score = models.FloatField(default=0.0)  # Bot's confidence in its response
    keywords_extracted = models.JSONField(default=list, blank=True)
    emotion_detected = models.JSONField(default=dict, blank=True)  # Emotion analysis results
    response_time = models.FloatField(null=True, blank=True)  # Time taken to generate response
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f'{self.sender}: {self.message[:50]}...'

class Achievement(models.Model):
    """Enhanced gamification achievements"""
    ACHIEVEMENT_TYPES = [
        ('streak', 'Check-in Streak'),
        ('conversation', 'Conversation Milestone'),
        ('gratitude', 'Gratitude Practice'),
        ('engagement', 'User Engagement'),
        ('wellness', 'Wellness Milestone'),
        ('social', 'Social Connection'),
        ('mindfulness', 'Mindfulness Practice'),
    ]
    
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary')
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🏆')
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    requirement_value = models.IntegerField(default=0)
    requirement_string = models.CharField(max_length=100, blank=True, null=True)
    points = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)  # Hidden until earned
    prerequisite = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.icon} {self.name}"

    def to_dict(self):
        return {
            'name': self.name, 
            'description': self.description, 
            'icon': self.icon, 
            'points': self.points,
            'rarity': self.rarity,
            'achievement_type': self.achievement_type
        }

class UserAchievement(models.Model):
    """User's earned achievements with progress tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    progress_value = models.FloatField(default=0.0)  # Current progress towards achievement
    is_new = models.BooleanField(default=True)
    celebration_shown = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} earned {self.achievement.name}"

class WellnessGoal(models.Model):
    """Enhanced user wellness goals with progress tracking"""
    GOAL_TYPES = [
        ('mood', 'Mood Improvement'),
        ('habits', 'Healthy Habits'),
        ('social', 'Social Connection'),
        ('mindfulness', 'Mindfulness Practice'),
        ('exercise', 'Physical Activity'),
        ('sleep', 'Sleep Quality'),
        ('custom', 'Custom Goal')
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('archived', 'Archived')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES, default='custom')
    target_value = models.IntegerField(null=True, blank=True)  # Target number (days, count, etc.)
    current_progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    target_date = models.DateField(null=True, blank=True)
    reminder_frequency = models.CharField(max_length=20, default='weekly')
    last_reminder_sent = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def progress_percentage(self):
        """Calculate progress as percentage"""
        if not self.target_value or self.target_value <= 0:
            return 0
        return min((self.current_progress / self.target_value) * 100, 100)

class CopingStrategy(models.Model):
    """Personalized coping strategies for users"""
    CATEGORY_CHOICES = [
        ('breathing', 'Breathing Exercises'),
        ('mindfulness', 'Mindfulness'),
        ('physical', 'Physical Activity'),
        ('social', 'Social Support'),
        ('cognitive', 'Cognitive Techniques'),
        ('creative', 'Creative Expression'),
        ('relaxation', 'Relaxation Techniques'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coping_strategies')
    title = models.CharField(max_length=100)
    description = models.TextField()
    instructions = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    effectiveness_rating = models.FloatField(default=0.0)  # User-rated effectiveness
    times_used = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class EmotionPattern(models.Model):
    """Track emotional patterns and triggers"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emotion_patterns')
    emotion = models.CharField(max_length=50)  # Primary emotion detected
    intensity = models.FloatField()  # Emotion intensity (0-1)
    context = models.TextField(blank=True)  # Context when emotion was detected
    triggers = models.JSONField(default=list)  # Identified triggers
    coping_used = models.ForeignKey(CopingStrategy, null=True, blank=True, on_delete=models.SET_NULL)
    outcome_rating = models.IntegerField(null=True, blank=True)  # How well user felt after (1-5)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.emotion} ({self.intensity:.2f})"

class CrisisResource(models.Model):
    """Crisis support resources with location-based filtering"""
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    country = models.CharField(max_length=50, default='US')
    availability = models.CharField(max_length=100, default='24/7')
    specialization = models.JSONField(default=list, blank=True)  # suicide, depression, etc.
    is_active = models.BooleanField(default=True)
    priority_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['priority_order', 'name']
    
    def __str__(self):
        return self.name

class BotPersonality(models.Model):
    """Enhanced configurable bot personality traits"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    # Time-based greetings
    greeting_morning = models.CharField(max_length=255, default="Good morning, {name}! Ready to start the day with a positive mindset?")
    greeting_afternoon = models.CharField(max_length=255, default="Good afternoon, {name}! Hope you're having a wonderful day.")
    greeting_evening = models.CharField(max_length=255, default="Good evening, {name}. Time to relax and reflect.")
    
    # Response templates
    positive_response = models.CharField(max_length=255, default="That's wonderful to hear, {name}! I'm so happy for you.")
    neutral_response = models.CharField(max_length=255, default="I understand. Thanks for sharing that with me, {name}.")
    supportive_response = models.CharField(max_length=255, default="I'm here for you, {name}. Remember to be kind to yourself.")
    empathetic_response = models.CharField(max_length=255, default="It sounds like you're going through a lot, {name}. I'm here to listen.")
    farewell_message = models.CharField(max_length=255, default="Take care, {name}. Remember I'm here whenever you need me.")
    
    # Specialized responses
    breathing_exercise_prompt = models.TextField(default="It sounds like a moment of calm could be helpful. Let's try a simple breathing exercise. Just breathe in for 4 seconds, hold for 4, and breathe out for 6. Let's do a few rounds together.")
    gratitude_prompt = models.TextField(default="That's a great idea. What is one small thing you're grateful for today, {name}?")
    crisis_response = models.TextField(default="It sounds like you are in a lot of pain, {name}. It's important to talk to someone who can help right now. You are not alone. Please reach out to one of these resources:\n{resources}")
    
    # Personality traits (0-1 scale)
    empathy_level = models.FloatField(default=0.8)
    humor_level = models.FloatField(default=0.5)
    formality_level = models.FloatField(default=0.3)
    proactivity_level = models.FloatField(default=0.6)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ConversationTemplate(models.Model):
    """Pre-built conversation templates for common scenarios"""
    TEMPLATE_TYPES = [
        ('crisis', 'Crisis Intervention'),
        ('check_in', 'Daily Check-in'),
        ('goal_setting', 'Goal Setting'),
        ('coping', 'Coping Strategies'),
        ('celebration', 'Achievement Celebration'),
        ('reflection', 'Reflection Exercise'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    trigger_keywords = models.JSONField(default=list)
    conversation_flow = models.JSONField(default=list)  # Step-by-step conversation flow
    personalization_fields = models.JSONField(default=list)  # Fields to personalize
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

# Content Models for dynamic responses
class MotivationalQuote(models.Model):
    text = models.TextField()
    author = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, default='general')
    mood_context = models.JSONField(default=list, blank=True)  # Which moods this works best for
    rating = models.FloatField(default=0.0)  # User ratings
    times_shown = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rating', 'times_shown']

    def __str__(self):
        return f'"{self.text[:50]}..." - {self.author}'

class Joke(models.Model):
    text = models.TextField()
    category = models.CharField(max_length=50, default='general')
    appropriateness_level = models.CharField(
        max_length=20, 
        choices=[('family', 'Family Friendly'), ('adult', 'Adult'), ('dark', 'Dark Humor')],
        default='family'
    )
    rating = models.FloatField(default=0.0)
    times_shown = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-rating', 'times_shown']
    
    def __str__(self):
        return self.text[:70]

class Affirmation(models.Model):
    text = models.TextField()
    category = models.CharField(max_length=50, default='general')
    target_emotion = models.JSONField(default=list, blank=True)  # What emotions this helps with
    rating = models.FloatField(default=0.0)
    times_shown = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rating', 'times_shown']

    def __str__(self):
        return self.text[:70]

class UserFeedback(models.Model):
    """Track user feedback on bot responses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    feedback_text = models.TextField(blank=True)
    improvement_suggestion = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback from {self.user.username} - {self.rating} stars"