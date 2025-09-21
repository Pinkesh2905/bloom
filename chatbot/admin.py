from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from .models import (
    UserProfile, MoodEntry, ConversationSession, ChatMessage, Achievement, 
    UserAchievement, WellnessGoal, CopingStrategy, EmotionPattern, CrisisResource, 
    BotPersonality, ConversationTemplate, MotivationalQuote, Joke, Affirmation, 
    UserFeedback
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_name', 'daily_check_in_streak', 'longest_streak', 'wellness_score', 'total_conversations', 'created_at']
    list_filter = ['mood_tracking_enabled', 'bot_personality', 'created_at']
    search_fields = ['user__username', 'user__email', 'preferred_name']
    readonly_fields = ['created_at', 'updated_at', 'wellness_score']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'preferred_name', 'timezone')
        }),
        ('Tracking Stats', {
            'fields': ('daily_check_in_streak', 'longest_streak', 'total_conversations', 'total_messages_sent', 'wellness_score')
        }),
        ('Settings', {
            'fields': ('mood_tracking_enabled', 'bot_personality', 'favorite_activities', 'privacy_settings')
        }),
        ('Timestamps', {
            'fields': ('last_check_in_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'bot_personality')

@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood', 'energy_level', 'stress_level', 'date', 'has_gratitude']
    list_filter = ['mood', 'energy_level', 'stress_level', 'physical_activity', 'social_interaction', 'date']
    search_fields = ['user__username', 'gratitude_note']
    date_hierarchy = 'date'
    
    def has_gratitude(self, obj):
        return bool(obj.gratitude_note)
    has_gratitude.boolean = True
    has_gratitude.short_description = 'Has Gratitude Note'

@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'title', 'start_time', 'message_count', 'sentiment_score', 'is_active']
    list_filter = ['is_active', 'start_time', 'crisis_flags']
    search_fields = ['user__username', 'session_id', 'title']
    readonly_fields = ['session_id', 'start_time', 'end_time']
    date_hierarchy = 'start_time'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'sender', 'message_preview', 'message_type', 'sentiment', 'timestamp']
    list_filter = ['sender', 'message_type', 'sentiment', 'timestamp']
    search_fields = ['user__username', 'message']
    readonly_fields = ['timestamp', 'response_time']
    date_hierarchy = 'timestamp'
    
    def message_preview(self, obj):
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message Preview'

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'achievement_type', 'rarity', 'points', 'requirement_value', 'is_active']
    list_filter = ['achievement_type', 'rarity', 'is_active', 'is_hidden']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon', 'achievement_type', 'rarity')
        }),
        ('Requirements', {
            'fields': ('requirement_value', 'requirement_string', 'prerequisite')
        }),
        ('Settings', {
            'fields': ('points', 'is_active', 'is_hidden')
        })
    )

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at', 'progress_value', 'is_new']
    list_filter = ['is_new', 'earned_at', 'achievement__achievement_type']
    search_fields = ['user__username', 'achievement__name']
    readonly_fields = ['earned_at']

@admin.register(WellnessGoal)
class WellnessGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'goal_type', 'progress_display', 'status', 'target_date']
    list_filter = ['goal_type', 'status', 'created_at']
    search_fields = ['user__username', 'title', 'description']
    
    def progress_display(self, obj):
        if obj.target_value:
            percentage = obj.progress_percentage()
            return format_html(
                '<div style="width: 100px; background: #f0f0f0; border-radius: 10px;">'
                '<div style="width: {}%; background: #10b981; height: 20px; border-radius: 10px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
                '{}%</div></div>',
                percentage, int(percentage)
            )
        return 'No target set'
    progress_display.short_description = 'Progress'

@admin.register(CopingStrategy)
class CopingStrategyAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'category', 'effectiveness_rating', 'times_used', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['user__username', 'title', 'description']

@admin.register(EmotionPattern)
class EmotionPatternAdmin(admin.ModelAdmin):
    list_display = ['user', 'emotion', 'intensity', 'coping_used', 'outcome_rating', 'timestamp']
    list_filter = ['emotion', 'timestamp']
    search_fields = ['user__username', 'emotion', 'context']
    readonly_fields = ['timestamp']

@admin.register(CrisisResource)
class CrisisResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'country', 'availability', 'priority_order', 'is_active']
    list_filter = ['country', 'is_active']
    search_fields = ['name', 'phone_number', 'description']
    list_editable = ['priority_order', 'is_active']

@admin.register(BotPersonality)
class BotPersonalityAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'empathy_level', 'humor_level', 'formality_level', 'proactivity_level']
    list_filter = ['is_default']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_default')
        }),
        ('Personality Traits (0-1 scale)', {
            'fields': ('empathy_level', 'humor_level', 'formality_level', 'proactivity_level')
        }),
        ('Time-based Greetings', {
            'fields': ('greeting_morning', 'greeting_afternoon', 'greeting_evening')
        }),
        ('Response Templates', {
            'fields': ('positive_response', 'neutral_response', 'supportive_response', 'empathetic_response', 'farewell_message'),
            'classes': ('collapse',)
        }),
        ('Specialized Responses', {
            'fields': ('breathing_exercise_prompt', 'gratitude_prompt', 'crisis_response'),
            'classes': ('collapse',)
        })
    )

@admin.register(ConversationTemplate)
class ConversationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'usage_count', 'is_active']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'trigger_keywords']

@admin.register(MotivationalQuote)
class MotivationalQuoteAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'author', 'category', 'rating', 'times_shown']
    list_filter = ['category', 'rating']
    search_fields = ['text', 'author']
    
    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Quote Preview'

@admin.register(Joke)
class JokeAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'category', 'appropriateness_level', 'rating', 'times_shown']
    list_filter = ['category', 'appropriateness_level', 'rating']
    search_fields = ['text']
    
    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Joke Preview'

@admin.register(Affirmation)
class AffirmationAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'category', 'rating', 'times_shown']
    list_filter = ['category', 'rating']
    search_fields = ['text']
    
    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Affirmation Preview'

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'message_preview', 'timestamp']
    list_filter = ['rating', 'timestamp']
    search_fields = ['user__username', 'feedback_text']
    readonly_fields = ['timestamp']
    
    def message_preview(self, obj):
        return obj.message.message[:50] + "..." if len(obj.message.message) > 50 else obj.message.message
    message_preview.short_description = 'Original Message'

# Custom admin site configuration
class ChatbotAdminSite(admin.AdminSite):
    site_header = 'Bloom Chatbot Administration'
    site_title = 'Bloom Admin'
    index_title = 'Welcome to Bloom Chatbot Administration'

# Register custom admin actions
def reset_user_streak(modeladmin, request, queryset):
    """Reset daily check-in streak for selected users"""
    count = queryset.update(daily_check_in_streak=0)
    modeladmin.message_user(request, f'Reset streak for {count} users.')
reset_user_streak.short_description = 'Reset daily check-in streak'

def recalculate_wellness_score(modeladmin, request, queryset):
    """Recalculate wellness score for selected users"""
    count = 0
    for profile in queryset:
        profile.calculate_wellness_score()
        count += 1
    modeladmin.message_user(request, f'Recalculated wellness score for {count} users.')
recalculate_wellness_score.short_description = 'Recalculate wellness score'

# Add custom actions to UserProfileAdmin
UserProfileAdmin.actions = [reset_user_streak, recalculate_wellness_score]

# Admin dashboard customizations
def admin_dashboard_stats(request):
    """Custom admin dashboard with key statistics"""
    from django.db.models import Count, Avg
    from datetime import date, timedelta
    
    # Get basic stats
    total_users = UserProfile.objects.count()
    active_sessions = ConversationSession.objects.filter(is_active=True).count()
    today_moods = MoodEntry.objects.filter(date=date.today()).count()
    
    # Weekly stats
    week_ago = date.today() - timedelta(days=7)
    weekly_messages = ChatMessage.objects.filter(timestamp__date__gte=week_ago).count()
    
    # Top achievements
    top_achievements = Achievement.objects.annotate(
        earned_count=Count('userachievement')
    ).order_by('-earned_count')[:5]
    
    # Crisis indicators
    crisis_messages = ChatMessage.objects.filter(
        message_type='crisis',
        timestamp__date__gte=week_ago
    ).count()
    
    return {
        'total_users': total_users,
        'active_sessions': active_sessions,
        'today_moods': today_moods,
        'weekly_messages': weekly_messages,
        'top_achievements': top_achievements,
        'crisis_messages': crisis_messages,
    }