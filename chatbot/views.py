import json
import re
import random
import logging
import time
import uuid
from datetime import date, timedelta, datetime
from collections import Counter, defaultdict

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count, Avg, F, Max
from django.core.paginator import Paginator
from django.db import transaction
from django.core.cache import cache
from django.conf import settings

from .models import (
    ChatMessage, UserProfile, MoodEntry, ConversationSession, 
    Achievement, UserAchievement, WellnessGoal, CrisisResource, BotPersonality,
    MotivationalQuote, Joke, Affirmation, CopingStrategy, EmotionPattern,
    ConversationTemplate, UserFeedback
)

# Setup logger for better debugging and monitoring
logger = logging.getLogger(__name__)

# Enhanced AI Logic Classes
class SentimentAnalyzer:
    """Advanced sentiment analysis with emotion detection"""
    
    def __init__(self):
        self.positive_words = {
            'happy': 2, 'joy': 2, 'love': 2, 'amazing': 2, 'wonderful': 2,
            'great': 1, 'good': 1, 'nice': 1, 'pleased': 1, 'content': 1,
            'excited': 2, 'thrilled': 2, 'grateful': 2, 'blessed': 2,
            'fantastic': 2, 'awesome': 2, 'brilliant': 2, 'perfect': 2,
            'excellent': 2, 'outstanding': 2, 'marvelous': 2, 'superb': 2
        }
        
        self.negative_words = {
            'sad': -2, 'depressed': -3, 'anxious': -2, 'worried': -2, 'scared': -2,
            'angry': -2, 'furious': -3, 'hate': -3, 'terrible': -3, 'awful': -3,
            'bad': -1, 'upset': -2, 'frustrated': -2, 'annoyed': -1, 'lonely': -2,
            'hopeless': -3, 'worthless': -3, 'helpless': -3, 'devastated': -3,
            'overwhelmed': -2, 'stressed': -2, 'panic': -3, 'crisis': -3
        }
        
        self.emotion_patterns = {
            'anxiety': ['worried', 'anxious', 'nervous', 'panic', 'scared', 'fear'],
            'depression': ['sad', 'depressed', 'hopeless', 'empty', 'worthless'],
            'anger': ['angry', 'mad', 'furious', 'rage', 'annoyed', 'frustrated'],
            'joy': ['happy', 'joy', 'excited', 'thrilled', 'elated', 'cheerful'],
            'gratitude': ['grateful', 'thankful', 'blessed', 'appreciative'],
            'love': ['love', 'adore', 'care', 'affection', 'cherish']
        }
        
        self.crisis_indicators = {
            'high': ['suicide', 'kill myself', 'end it all', 'want to die', 'better off dead'],
            'medium': ['hurt myself', 'self harm', 'cutting', 'no point living', 'give up'],
            'low': ['hopeless', 'worthless', 'nobody cares', "can't go on"]
        }
    
    def analyze(self, text):
        """Comprehensive sentiment and emotion analysis"""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Sentiment scoring
        sentiment_score = 0
        word_count = len(words)
        
        for word in words:
            if word in self.positive_words:
                sentiment_score += self.positive_words[word]
            elif word in self.negative_words:
                sentiment_score += self.negative_words[word]
        
        # Normalize sentiment (-1 to 1)
        normalized_sentiment = max(-1, min(1, sentiment_score / max(word_count, 1)))
        
        # Emotion detection
        emotions_detected = {}
        for emotion, patterns in self.emotion_patterns.items():
            count = sum(1 for pattern in patterns if pattern in text_lower)
            if count > 0:
                emotions_detected[emotion] = min(1.0, count / len(patterns))
        
        # Crisis assessment
        crisis_level = 'none'
        crisis_confidence = 0.0
        
        for level, indicators in self.crisis_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    crisis_level = level
                    crisis_confidence = 0.9 if level == 'high' else 0.7 if level == 'medium' else 0.5
                    break
            if crisis_level != 'none':
                break
        
        return {
            'sentiment_score': normalized_sentiment,
            'sentiment_label': self._get_sentiment_label(normalized_sentiment),
            'emotions': emotions_detected,
            'crisis_level': crisis_level,
            'crisis_confidence': crisis_confidence,
            'confidence': abs(normalized_sentiment) if normalized_sentiment != 0 else 0.5
        }
    
    def _get_sentiment_label(self, score):
        if score >= 0.5: return 'very_positive'
        elif score >= 0.1: return 'positive'
        elif score <= -0.5: return 'very_negative'
        elif score <= -0.1: return 'negative'
        else: return 'neutral'

class ConversationContext:
    """Manages conversation context and memory"""
    
    def __init__(self, session):
        self.session = session
        self.recent_messages = []
        self.topics_discussed = set()
        self.user_preferences = {}
        self.conversation_flow = []
    
    def load_context(self):
        """Load recent conversation context"""
        messages = ChatMessage.objects.filter(
            session=self.session
        ).order_by('-timestamp')[:10]
        
        self.recent_messages = [
            {
                'sender': msg.sender,
                'message': msg.message,
                'message_type': msg.message_type,
                'sentiment': msg.sentiment,
                'timestamp': msg.timestamp
            }
            for msg in messages
        ]
        
        # Extract topics from keywords
        for msg in messages:
            if msg.keywords_extracted:
                self.topics_discussed.update(msg.keywords_extracted)
    
    def get_conversation_summary(self):
        """Generate a summary of recent conversation"""
        if not self.recent_messages:
            return "New conversation"
        
        recent_topics = list(self.topics_discussed)[-5:]
        sentiment_trend = [msg.get('sentiment', 'neutral') for msg in self.recent_messages[-3:]]
        
        return {
            'recent_topics': recent_topics,
            'sentiment_trend': sentiment_trend,
            'message_count': len(self.recent_messages)
        }

class ResponseGenerator:
    """Advanced response generation with contextual awareness"""
    
    def __init__(self, user_profile, personality, sentiment_analyzer):
        self.profile = user_profile
        self.personality = personality
        self.sentiment_analyzer = sentiment_analyzer
        self.response_templates = self._load_response_templates()
    
    def _load_response_templates(self):
        """Load response templates based on context"""
        return {
            'crisis_high': [
                "I'm very concerned about what you're sharing, {name}. Your life has value and you matter. Please reach out to a crisis helpline right now: {resources}",
                "What you're feeling is real and valid, but there are people who can help you through this. Please don't face this alone: {resources}",
            ],
            'crisis_medium': [
                "I'm worried about you, {name}. It sounds like you're in a lot of pain right now. Have you considered talking to a counselor or calling a support line?",
                "These feelings you're describing are serious, {name}. You deserve support. Here are some resources that might help: {resources}",
            ],
            'empathy_high': [
                "I can really hear the pain in your words, {name}. What you're going through sounds incredibly difficult.",
                "That sounds so challenging, {name}. I want you to know that your feelings are completely valid.",
                "I'm sitting with you in this difficult moment, {name}. You don't have to carry this burden alone.",
            ],
            'encouragement': [
                "You've shown such strength by sharing this with me, {name}. That takes real courage.",
                "Even in the midst of this difficulty, I can see your resilience, {name}. You're stronger than you know.",
                "You're taking important steps by talking about this, {name}. That's something to be proud of.",
            ],
            'check_in': [
                "How has your day been treating you, {name}?",
                "I've been thinking about our last conversation, {name}. How are you feeling now?",
                "What's been on your mind lately, {name}?",
            ]
        }
    
    def generate_response(self, user_message, context, analysis_result):
        """Generate contextually appropriate response"""
        name = self.profile.preferred_name
        
        # Handle crisis situations first
        if analysis_result['crisis_level'] != 'none':
            return self._handle_crisis_response(name, analysis_result['crisis_level'])
        
        # Handle specific emotions
        if analysis_result['emotions']:
            dominant_emotion = max(analysis_result['emotions'].items(), key=lambda x: x[1])
            return self._handle_emotional_response(user_message, dominant_emotion, name, context)
        
        # Handle based on sentiment
        sentiment = analysis_result['sentiment_label']
        if sentiment in ['very_negative', 'negative']:
            return self._generate_supportive_response(user_message, name, context)
        elif sentiment in ['positive', 'very_positive']:
            return self._generate_positive_response(user_message, name, context)
        else:
            return self._generate_neutral_response(user_message, name, context)
    
    def _handle_crisis_response(self, name, crisis_level):
        """Handle crisis intervention"""
        resources = CrisisResource.objects.filter(is_active=True)[:3]
        resources_text = "\n".join([
            f"• {r.name}: {r.phone_number}" 
            for r in resources
        ]) if resources.exists() else "• National Suicide Prevention Lifeline: 988"
        
        template_key = f'crisis_{crisis_level}'
        templates = self.response_templates.get(template_key, self.response_templates['crisis_high'])
        response = random.choice(templates).format(name=name, resources=resources_text)
        
        return response, 'crisis', {
            'crisis_level': crisis_level,
            'crisis_resources': list(resources.values('name', 'phone_number'))
        }
    
    def _handle_emotional_response(self, user_message, dominant_emotion, name, context):
        """Handle responses based on detected emotion"""
        emotion_name, intensity = dominant_emotion
        
        if emotion_name == 'anxiety':
            return self._generate_anxiety_response(name, intensity)
        elif emotion_name == 'depression':
            return self._generate_depression_response(name, intensity)
        elif emotion_name == 'anger':
            return self._generate_anger_response(name, intensity)
        elif emotion_name == 'joy':
            return self._generate_joy_response(name, intensity)
        elif emotion_name == 'gratitude':
            return self._generate_gratitude_response(name, intensity)
        else:
            return self._generate_neutral_response(user_message, name, context)
    
    def _generate_anxiety_response(self, name, intensity):
        """Generate anxiety-specific response"""
        if intensity > 0.7:
            response = f"I can sense you're feeling quite anxious right now, {name}. Let's try to slow things down together. Would a breathing exercise help you feel more grounded?"
            return response, 'breathing', {'suggested_technique': 'deep_breathing'}
        else:
            response = f"I notice some anxiety in what you're sharing, {name}. What's been weighing on your mind?"
            return response, 'therapy', {}
    
    def _generate_depression_response(self, name, intensity):
        """Generate depression-specific response"""
        templates = self.response_templates['empathy_high']
        response = random.choice(templates).format(name=name)
        return response, 'therapy', {'suggested_coping': 'gentle_activity'}
    
    def _generate_anger_response(self, name, intensity):
        """Generate anger management response"""
        if intensity > 0.6:
            response = f"I can hear the frustration and anger in your words, {name}. Those feelings are valid. Sometimes it helps to take a step back and breathe. What triggered these feelings?"
            return response, 'therapy', {'suggested_technique': 'anger_management'}
        else:
            response = f"It sounds like something's really bothering you, {name}. I'm here to listen if you want to talk about it."
            return response, 'general', {}
    
    def _generate_joy_response(self, name, intensity):
        """Generate positive reinforcement response"""
        responses = [
            f"I love hearing the happiness in your words, {name}! What's been bringing you such joy?",
            f"Your positive energy is wonderful, {name}! It's beautiful to see you feeling so good.",
            f"That's fantastic, {name}! I'm so glad you're experiencing such happiness."
        ]
        return random.choice(responses), 'general', {}
    
    def _generate_gratitude_response(self, name, intensity):
        """Generate gratitude-focused response"""
        response = f"I can feel the gratitude in your words, {name}. There's something so powerful about recognizing the good things in our lives. What else are you appreciating today?"
        return response, 'gratitude', {}
    
    def _generate_supportive_response(self, user_message, name, context):
        """Generate supportive response for negative sentiment"""
        templates = self.response_templates['empathy_high']
        base_response = random.choice(templates).format(name=name)
        
        # Add contextual follow-up
        if 'work' in user_message.lower() or 'job' in user_message.lower():
            follow_up = " Work stress can be really overwhelming. What's been the most challenging part?"
        elif 'relationship' in user_message.lower() or 'friend' in user_message.lower():
            follow_up = " Relationship challenges can be so difficult. How are you taking care of yourself through this?"
        else:
            follow_up = " What would feel most helpful for you right now?"
        
        return base_response + follow_up, 'therapy', {}
    
    def _generate_positive_response(self, user_message, name, context):
        """Generate response for positive sentiment"""
        responses = [
            f"It's wonderful to hear such positivity from you, {name}! What's been going well?",
            f"I can feel the good energy in your words, {name}! Tell me more about what's been positive.",
            f"That's fantastic, {name}! I love celebrating these moments with you."
        ]
        return random.choice(responses), 'general', {}
    
    def _generate_neutral_response(self, user_message, name, context):
        """Generate neutral conversational response"""
        if any(word in user_message.lower() for word in ['how', 'what', 'why', 'when', 'where']):
            responses = [
                f"That's an interesting question, {name}. Let me think about that with you.",
                f"I appreciate you asking that, {name}. What's prompting this question?",
                f"That makes me curious too, {name}. What are your thoughts on it?"
            ]
        else:
            responses = [
                f"I hear you, {name}. Tell me more about that.",
                f"Thanks for sharing that with me, {name}. What's been on your mind about this?",
                f"I'm listening, {name}. How are you feeling about all of this?"
            ]
        
        return random.choice(responses), 'general', {}

# Enhanced Helper Functions
def get_or_create_user_profile(user):
    """Enhanced profile creation with better defaults"""
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'preferred_name': user.first_name or user.username.title(),
            'total_conversations': 0,
            'privacy_settings': {
                'share_mood_patterns': True,
                'anonymous_feedback': True,
                'data_retention_days': 365
            }
        }
    )
    
    if created:
        # Create default personality if none exists
        default_personality, _ = BotPersonality.objects.get_or_create(
            is_default=True,
            defaults={
                'name': 'Bloom (Default)',
                'description': 'Empathetic and supportive wellness companion',
                'empathy_level': 0.8,
                'humor_level': 0.4,
                'formality_level': 0.2,
                'proactivity_level': 0.6
            }
        )
        profile.bot_personality = default_personality
        profile.save()
        
        logger.info(f"Created new user profile for {user.username}")
    
    return profile

def get_current_session(request, session_id_from_client=None):
    """Enhanced session management with better context tracking"""
    if session_id_from_client:
        try:
            session_uuid = uuid.UUID(session_id_from_client)
        except ValueError:
            # Invalid UUID, create new session
            session_uuid = uuid.uuid4()
            session_id_from_client = str(session_uuid)
        
        session, created = ConversationSession.objects.get_or_create(
            user=request.user,
            session_id=session_uuid,
            defaults={
                'start_time': timezone.now(),
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Created new session {session_id_from_client} for user {request.user.id}")
        
        return session
    
    # Create new session with UUID
    session_uuid = uuid.uuid4()
    session = ConversationSession.objects.create(
        user=request.user,
        session_id=session_uuid,
        start_time=timezone.now(),
        is_active=True
    )
    
    logger.info(f"Created new fallback session {session_uuid} for user {request.user.id}")
    return session

def extract_keywords(text):
    """Extract relevant keywords from user message"""
    # Common stop words to ignore
    stop_words = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
        'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
        'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down', 'in', 'out',
        'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once'
    }
    
    # Extract words, filter out stop words and short words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Return most frequent keywords (up to 5)
    keyword_counts = Counter(keywords)
    return [word for word, count in keyword_counts.most_common(5)]

@transaction.atomic
def check_and_award_achievements(user, event_type, **kwargs):
    """Enhanced achievement system with more sophisticated logic"""
    profile = get_or_create_user_profile(user)
    newly_awarded = []
    
    # Get user's current achievements
    earned_achievement_ids = set(
        UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    )
    
    # Get potential achievements (not yet earned, active, prerequisites met)
    potential_achievements = Achievement.objects.filter(
        is_active=True
    ).exclude(
        id__in=earned_achievement_ids
    )
    
    # Filter by prerequisites
    for achievement in potential_achievements:
        if achievement.prerequisite_id and achievement.prerequisite_id not in earned_achievement_ids:
            continue
        
        should_award = False
        
        if event_type == 'mood_entry' and achievement.achievement_type == 'streak':
            should_award = profile.daily_check_in_streak >= achievement.requirement_value
            
        elif event_type == 'conversation_start' and achievement.achievement_type == 'conversation':
            should_award = profile.total_conversations >= achievement.requirement_value
            
        elif event_type == 'gratitude_practice' and achievement.achievement_type == 'gratitude':
            gratitude_count = ChatMessage.objects.filter(
                user=user, 
                message_type='gratitude'
            ).count()
            should_award = gratitude_count >= achievement.requirement_value
            
        elif event_type == 'wellness_milestone' and achievement.achievement_type == 'wellness':
            should_award = profile.wellness_score >= achievement.requirement_value
            
        elif event_type == 'long_conversation' and achievement.achievement_type == 'engagement':
            session = kwargs.get('session')
            if session and achievement.requirement_string == 'long_conversation':
                should_award = session.message_count >= 20
        
        if should_award:
            user_achievement = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                progress_value=100.0
            )
            newly_awarded.append(achievement)
            
            logger.info(f"Awarded achievement '{achievement.name}' to user {user.id}")
    
    return newly_awarded

def get_personalized_content(user, content_type, context=None):
    """Get personalized content based on user history and preferences"""
    profile = get_or_create_user_profile(user)
    
    if content_type == 'motivational_quote':
        # Get quotes that match user's current mood context
        recent_mood = MoodEntry.objects.filter(user=user).order_by('-date').first()
        if recent_mood:
            quotes = MotivationalQuote.objects.filter(
                mood_context__contains=[recent_mood.mood]
            ).order_by('-rating', 'times_shown')[:5]
        else:
            quotes = MotivationalQuote.objects.order_by('-rating', 'times_shown')[:5]
        
        if quotes:
            quote = random.choice(quotes)
            quote.times_shown = F('times_shown') + 1
            quote.save()
            return quote
    
    elif content_type == 'joke':
        jokes = Joke.objects.filter(
            appropriateness_level='family'
        ).order_by('-rating', 'times_shown')[:10]
        
        if jokes:
            joke = random.choice(jokes)
            joke.times_shown = F('times_shown') + 1
            joke.save()
            return joke
    
    elif content_type == 'affirmation':
        # Get affirmations based on detected emotions
        if context and 'emotions' in context:
            target_emotions = list(context['emotions'].keys())
            affirmations = Affirmation.objects.filter(
                target_emotion__overlap=target_emotions
            ).order_by('-rating', 'times_shown')[:5]
        else:
            affirmations = Affirmation.objects.order_by('-rating', 'times_shown')[:5]
        
        if affirmations:
            affirmation = random.choice(affirmations)
            affirmation.times_shown = F('times_shown') + 1
            affirmation.save()
            return affirmation
    
    return None

# Enhanced Bot Reply Logic
def get_contextual_bot_reply(user_msg, profile, session):
    """Enhanced contextual reply generation with advanced AI logic"""
    start_time = time.time()
    
    # Initialize AI components
    sentiment_analyzer = SentimentAnalyzer()
    context = ConversationContext(session)
    context.load_context()
    
    # Analyze user message
    analysis_result = sentiment_analyzer.analyze(user_msg)
    keywords = extract_keywords(user_msg)
    
    # Generate response
    personality = profile.bot_personality or BotPersonality.objects.filter(is_default=True).first()
    response_generator = ResponseGenerator(profile, personality, sentiment_analyzer)
    
    bot_reply, reply_type, metadata = response_generator.generate_response(
        user_msg, context, analysis_result
    )
    
    # Handle special cases
    user_msg_lower = user_msg.lower()
    
    # Greeting detection
    if any(word in user_msg_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        bot_reply, reply_type = handle_greeting(profile.preferred_name, personality)
        
    # Farewell detection
    elif any(word in user_msg_lower for word in ["bye", "goodbye", "see you", "talk later"]):
        bot_reply = personality.farewell_message.format(name=profile.preferred_name)
        reply_type = 'general'
        
    # Specific action requests
    elif 'breathing' in user_msg_lower or 'breathe' in user_msg_lower:
        bot_reply = personality.breathing_exercise_prompt.format(name=profile.preferred_name)
        reply_type = 'breathing'
        metadata.update({'exercise_type': 'breathing', 'duration': '5_minutes'})
        
    elif 'joke' in user_msg_lower or 'funny' in user_msg_lower:
        joke = get_personalized_content(profile.user, 'joke')
        if joke:
            bot_reply = f"Here's something to brighten your day, {profile.preferred_name}: {joke.text}"
        else:
            bot_reply = f"I wish I had a good joke for you right now, {profile.preferred_name}! But I'm still here to chat and support you."
        reply_type = 'joke'
        
    elif 'quote' in user_msg_lower or 'motivat' in user_msg_lower:
        quote = get_personalized_content(profile.user, 'motivational_quote')
        if quote:
            author_text = f" - {quote.author}" if quote.author else ""
            bot_reply = f'"{quote.text}"{author_text}\n\nI hope this resonates with you today, {profile.preferred_name}.'
        else:
            bot_reply = f"You're already showing strength by reaching out, {profile.preferred_name}. That's something to be proud of."
        reply_type = 'motivation'
        
    elif 'grateful' in user_msg_lower or 'gratitude' in user_msg_lower:
        bot_reply = personality.gratitude_prompt.format(name=profile.preferred_name)
        reply_type = 'gratitude'
    
    # Add response timing
    response_time = time.time() - start_time
    metadata.update({
        'response_time': response_time,
        'keywords': keywords,
        'sentiment_analysis': analysis_result,
        'confidence_score': analysis_result.get('confidence', 0.5)
    })
    
    return bot_reply, reply_type, metadata

def handle_greeting(name, personality):
    """Enhanced time-aware greeting with personalization"""
    current_hour = timezone.now().hour
    
    if 5 <= current_hour < 12:
        greeting = personality.greeting_morning.format(name=name)
    elif 12 <= current_hour < 17:
        greeting = personality.greeting_afternoon.format(name=name)
    else:
        greeting = personality.greeting_evening.format(name=name)
    
    return greeting, 'general'

# Django Views (API Endpoints)
@login_required
def chatbot_view(request):
    """Enhanced main chatbot interface"""
    profile = get_or_create_user_profile(request.user)
    today_mood = MoodEntry.objects.filter(user=request.user, date=date.today()).first()
    
    # Update wellness score
    profile.calculate_wellness_score()
    
    context = {
        'profile': profile,
        'today_mood': today_mood,
        'wellness_score': round(profile.wellness_score, 1),
        'longest_streak': profile.longest_streak,
    }
    return render(request, 'chatbot/chatbot.html', context)

@csrf_exempt
@login_required
@transaction.atomic
def send_message(request):
    """Enhanced message handling with advanced AI processing"""
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        user_msg = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_msg:
            return JsonResponse({"error": "Empty message"}, status=400)
        
        if len(user_msg) > 1000:  # Prevent extremely long messages
            return JsonResponse({"error": "Message too long"}, status=400)
        
        profile = get_or_create_user_profile(request.user)
        session = get_current_session(request, session_id)
        
        # Create user message with enhanced analysis
        sentiment_analyzer = SentimentAnalyzer()
        analysis = sentiment_analyzer.analyze(user_msg)
        keywords = extract_keywords(user_msg)
        
        user_message = ChatMessage.objects.create(
            session=session,
            user=request.user,
            sender="user",
            message=user_msg,
            sentiment=analysis['sentiment_label'],
            keywords_extracted=keywords,
            emotion_detected=analysis['emotions'],
        )
        
        # Generate bot response
        bot_reply, reply_type, metadata = get_contextual_bot_reply(user_msg, profile, session)
        
        # Create bot message
        bot_message = ChatMessage.objects.create(
            session=session,
            user=request.user,
            sender="bot",
            message=bot_reply,
            message_type=reply_type,
            confidence_score=metadata.get('confidence_score', 0.5),
            response_time=metadata.get('response_time', 0),
            metadata=metadata
        )
        
        # Update session stats
        if session.message_count == 0:
            profile.total_conversations += 1
            profile.save()
            session.update_title()
        
        session.message_count += 2
        session.end_time = timezone.now()
        session.save()
        
        # Update user stats
        profile.total_messages_sent += 1
        profile.save()
        
        # Check for achievements
        new_achievements = check_and_award_achievements(request.user, 'conversation_start')
        
        if reply_type == 'gratitude':
            new_achievements.extend(check_and_award_achievements(request.user, 'gratitude_practice'))
        
        if session.message_count >= 20:
            new_achievements.extend(check_and_award_achievements(request.user, 'long_conversation', session=session))
        
        # Track emotion patterns if significant emotion detected
        if analysis['emotions']:
            dominant_emotion = max(analysis['emotions'].items(), key=lambda x: x[1])
            EmotionPattern.objects.create(
                user=request.user,
                emotion=dominant_emotion[0],
                intensity=dominant_emotion[1],
                context=user_msg[:200],  # Store context snippet
                triggers=keywords[:3]  # Top 3 keywords as potential triggers
            )
        
        response_data = {
            "reply": bot_reply,
            "message_type": reply_type,
            "metadata": {
                k: v for k, v in metadata.items() 
                if k not in ['sentiment_analysis']  # Don't expose internal analysis
            },
            "new_achievements": [ach.to_dict() for ach in new_achievements],
            "session_id": str(session.session_id)
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        logger.warning("Invalid JSON received in send_message")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error in send_message: {e}", exc_info=True)
        return JsonResponse({"error": "An internal error occurred"}, status=500)

@login_required
def get_session_history_api(request):
    """Enhanced session history with better metadata"""
    sessions = ConversationSession.objects.filter(
        user=request.user,
        is_active=True
    ).annotate(
        msg_count=Count('chatmessage')
    ).filter(
        msg_count__gt=0
    ).order_by('-start_time')[:20]
    
    session_data = []
    for session in sessions:
        first_message = session.chatmessage_set.filter(sender='user').first()
        title = session.title or (first_message.message[:40] + "..." if first_message and len(first_message.message) > 40 else first_message.message if first_message else "Chat")
        
        session_data.append({
            'session_id': str(session.session_id),
            'start_time': session.start_time.strftime('%b %d, %Y %I:%M %p'),
            'title': title,
            'message_count': session.message_count,
            'sentiment_score': round(session.sentiment_score, 2) if session.sentiment_score else 0,
            'topics': session.topics_discussed[:3] if session.topics_discussed else []
        })
    
    return JsonResponse({"sessions": session_data})

@login_required
def get_chat_history_api(request):
    """Enhanced chat history retrieval"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({"error": "Session ID required"}, status=400)
    
    try:
        session_uuid = uuid.UUID(session_id)
        session = ConversationSession.objects.get(
            user=request.user,
            session_id=session_uuid
        )
    except (ValueError, ConversationSession.DoesNotExist):
        return JsonResponse({"error": "Invalid session ID"}, status=400)
    
    messages = ChatMessage.objects.filter(
        session=session
    ).order_by('timestamp').select_related('session')
    
    message_data = []
    for msg in messages:
        message_data.append({
            'sender': msg.sender,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%I:%M %p'),
            'message_type': msg.message_type,
            'sentiment': msg.sentiment if msg.sender == 'user' else None
        })
    
    return JsonResponse({
        "messages": message_data,
        "session_title": session.title or "Chat",
        "message_count": len(message_data)
    })

@csrf_exempt
@login_required
@transaction.atomic
def clear_chat_history_api(request):
    """Enhanced chat history clearing with confirmation"""
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        confirm = data.get('confirm', False)
        
        if not confirm:
            return JsonResponse({"error": "Confirmation required"}, status=400)
        
        # Archive instead of delete for data recovery
        user_sessions = ConversationSession.objects.filter(user=request.user)
        ChatMessage.objects.filter(session__in=user_sessions).update(
            metadata=F('metadata') | {'archived': True, 'archived_at': timezone.now().isoformat()}
        )
        user_sessions.update(is_active=False)
        
        logger.info(f"Archived chat history for user {request.user.id}")
        return JsonResponse({"status": "cleared"})
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}", exc_info=True)
        return JsonResponse({"error": "An internal error occurred"}, status=500)

@csrf_exempt
@login_required
@transaction.atomic
def save_mood_entry_api(request):
    """Enhanced mood entry saving with analytics"""
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        mood = data.get('mood')
        if not mood or mood not in dict(MoodEntry.MOOD_CHOICES):
            return JsonResponse({"error": "Invalid mood value"}, status=400)
        
        # Create or update mood entry
        mood_entry, created = MoodEntry.objects.update_or_create(
            user=request.user,
            date=date.today(),
            defaults={
                'mood': mood,
                'energy_level': max(1, min(5, int(data.get('energy_level', 3)))),
                'stress_level': max(1, min(5, int(data.get('stress_level', 3)))),
                'gratitude_note': data.get('gratitude_note', '').strip()[:500],
                'sleep_hours': data.get('sleep_hours'),
                'physical_activity': data.get('physical_activity', False),
                'social_interaction': data.get('social_interaction', False),
                'mood_triggers': data.get('mood_triggers', [])
            }
        )
        
        profile = get_or_create_user_profile(request.user)
        
        # Update streak
        if created:
            profile.update_streak()
        
        # Update wellness score
        profile.calculate_wellness_score()
        
        # Check for achievements
        new_achievements = check_and_award_achievements(request.user, 'mood_entry')
        
        # Generate contextual follow-up message
        name = profile.preferred_name
        follow_up_message = f"Thank you for checking in, {name}! "
        
        if mood_entry.stress_level >= 4:
            follow_up_message += "I notice your stress level is quite high. Would you like to try a breathing exercise or talk about what's causing the stress?"
        elif mood_entry.energy_level <= 2:
            follow_up_message += "Your energy seems low today. Have you been getting enough rest? Sometimes gentle movement can help too."
        elif mood in ['terrible', 'bad']:
            follow_up_message += "I'm sorry you're feeling this way. Remember that difficult feelings are temporary. I'm here to listen if you want to talk."
        elif mood_entry.gratitude_note:
            follow_up_message += "It's wonderful that you took time for gratitude. That's such a powerful practice for wellbeing."
        elif mood in ['great', 'amazing']:
            follow_up_message += f"I love hearing that you're feeling {mood} today! What's contributing to this positive mood?"
        else:
            follow_up_message += "Thanks for sharing how you're feeling. Every check-in helps build awareness of your patterns."
        
        # Check for wellness milestones
        if profile.wellness_score >= 75:
            wellness_achievements = check_and_award_achievements(request.user, 'wellness_milestone')
            new_achievements.extend(wellness_achievements)
        
        return JsonResponse({
            "status": "saved",
            "streak": profile.daily_check_in_streak,
            "longest_streak": profile.longest_streak,
            "wellness_score": round(profile.wellness_score, 1),
            "is_new": created,
            "follow_up_message": follow_up_message,
            "new_achievements": [ach.to_dict() for ach in new_achievements]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error in save_mood_entry: {e}", exc_info=True)
        return JsonResponse({"error": "An internal error occurred"}, status=500)

@login_required
def get_mood_patterns_api(request):
    """Advanced mood analytics and pattern recognition"""
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    mood_entries = MoodEntry.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    if mood_entries.count() < 7:
        return JsonResponse({
            "patterns": [],
            "message": "Keep checking in regularly to unlock your mood patterns and insights!",
            "entries_needed": 7 - mood_entries.count()
        })
    
    # Mood scoring for analysis
    mood_values = {'terrible': 1, 'bad': 2, 'okay': 3, 'good': 4, 'great': 5, 'amazing': 6}
    
    patterns = []
    insights = []
    
    # Day of week analysis
    day_moods = defaultdict(list)
    for entry in mood_entries:
        day_moods[entry.date.weekday()].append(mood_values[entry.mood])
    
    if len(day_moods) >= 5:  # Need data from at least 5 different days
        avg_day_moods = {}
        for day, moods in day_moods.items():
            if len(moods) >= 2:  # Need at least 2 data points
                avg_day_moods[day] = sum(moods) / len(moods)
        
        if avg_day_moods:
            best_day = max(avg_day_moods.items(), key=lambda x: x[1])
            worst_day = min(avg_day_moods.items(), key=lambda x: x[1])
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            if best_day[1] > 4.0:
                patterns.append(f"✨ {day_names[best_day[0]]}s tend to be your best days!")
            
            if worst_day[1] < 2.5 and best_day[0] != worst_day[0]:
                patterns.append(f"💙 {day_names[worst_day[0]]}s seem more challenging. Consider planning extra self-care on these days.")
    
    # Streak analysis
    recent_moods = [mood_values[entry.mood] for entry in mood_entries[:14]]
    if len(recent_moods) >= 7:
        avg_recent = sum(recent_moods) / len(recent_moods)
        if avg_recent > 4.0:
            patterns.append("🌟 You've been maintaining consistently positive moods lately!")
        elif avg_recent < 2.5:
            insights.append("I've noticed your mood has been lower recently. Consider reaching out to someone you trust or a professional for support.")
    
    # Stress and energy correlation
    stress_energy_data = [(entry.stress_level, entry.energy_level, mood_values[entry.mood]) for entry in mood_entries[:30]]
    if len(stress_energy_data) >= 10:
        high_stress_moods = [mood for stress, energy, mood in stress_energy_data if stress >= 4]
        low_energy_moods = [mood for stress, energy, mood in stress_energy_data if energy <= 2]
        
        if len(high_stress_moods) >= 5:
            avg_high_stress_mood = sum(high_stress_moods) / len(high_stress_moods)
            if avg_high_stress_mood < 3.0:
                insights.append("High stress levels seem to significantly impact your mood. Stress management techniques might be helpful.")
        
        if len(low_energy_moods) >= 5:
            avg_low_energy_mood = sum(low_energy_moods) / len(low_energy_moods)
            if avg_low_energy_mood < 3.0:
                insights.append("Low energy days often correlate with lower moods. Focus on sleep quality and gentle movement.")
    
    # Gratitude impact analysis
    gratitude_entries = [entry for entry in mood_entries[:30] if entry.gratitude_note]
    non_gratitude_entries = [entry for entry in mood_entries[:30] if not entry.gratitude_note]
    
    if len(gratitude_entries) >= 5 and len(non_gratitude_entries) >= 5:
        avg_gratitude_mood = sum(mood_values[entry.mood] for entry in gratitude_entries) / len(gratitude_entries)
        avg_regular_mood = sum(mood_values[entry.mood] for entry in non_gratitude_entries) / len(non_gratitude_entries)
        
        if avg_gratitude_mood > avg_regular_mood + 0.5:
            patterns.append("🙏 Days when you practice gratitude tend to have better mood scores!")
    
    # Weekly trend analysis
    if len(mood_entries) >= 14:
        recent_week = mood_entries[:7]
        previous_week = mood_entries[7:14]
        
        recent_avg = sum(mood_values[entry.mood] for entry in recent_week) / 7
        previous_avg = sum(mood_values[entry.mood] for entry in previous_week) / 7
        
        if recent_avg > previous_avg + 0.5:
            patterns.append("📈 Your mood has been trending upward this week!")
        elif recent_avg < previous_avg - 0.5:
            insights.append("📉 Your mood has been lower this week. Consider what support might be helpful.")
    
    return JsonResponse({
        "patterns": patterns,
        "insights": insights,
        "total_entries": mood_entries.count(),
        "analysis_period": f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
    })

@login_required
def get_achievements_api(request):
    """Enhanced achievements API with progress tracking"""
    user_achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('achievement').order_by('-earned_at')
    
    total_points = sum(ua.achievement.points for ua in user_achievements)
    
    # Get available achievements user hasn't earned yet
    earned_ids = set(ua.achievement.id for ua in user_achievements)
    available_achievements = Achievement.objects.filter(
        is_active=True,
        is_hidden=False
    ).exclude(id__in=earned_ids)[:5]  # Show next 5 achievements
    
    # Mark new achievements as viewed
    user_achievements.filter(is_new=True).update(is_new=False)
    
    achievement_data = []
    for ua in user_achievements:
        ach_data = ua.achievement.to_dict()
        ach_data.update({
            'earned_at': ua.earned_at.strftime('%b %d, %Y'),
            'is_new': ua.is_new,
            'progress': ua.progress_value
        })
        achievement_data.append(ach_data)
    
    available_data = []
    profile = get_or_create_user_profile(request.user)
    
    for ach in available_achievements:
        progress = 0
        if ach.achievement_type == 'streak':
            progress = min(100, (profile.daily_check_in_streak / ach.requirement_value) * 100)
        elif ach.achievement_type == 'conversation':
            progress = min(100, (profile.total_conversations / ach.requirement_value) * 100)
        
        available_data.append({
            'name': ach.name,
            'description': ach.description,
            'icon': ach.icon,
            'points': ach.points,
            'progress': round(progress, 1),
            'requirement_value': ach.requirement_value,
            'achievement_type': ach.achievement_type
        })
    
    return JsonResponse({
        "achievements": achievement_data,
        "available_achievements": available_data,
        "total_points": total_points,
        "total_achievements": len(achievement_data)
    })

@login_required
def get_wellness_insights_api(request):
    """New endpoint for wellness insights and recommendations"""
    profile = get_or_create_user_profile(request.user)
    
    # Get recent mood data
    recent_moods = MoodEntry.objects.filter(
        user=request.user,
        date__gte=date.today() - timedelta(days=30)
    ).order_by('-date')
    
    insights = []
    recommendations = []
    
    if recent_moods.count() >= 7:
        mood_values = {'terrible': 1, 'bad': 2, 'okay': 3, 'good': 4, 'great': 5, 'amazing': 6}
        avg_mood = sum(mood_values[mood.mood] for mood in recent_moods) / recent_moods.count()
        avg_stress = sum(mood.stress_level for mood in recent_moods) / recent_moods.count()
        avg_energy = sum(mood.energy_level for mood in recent_moods) / recent_moods.count()
        
        # Generate insights based on patterns
        if avg_mood < 3.0:
            insights.append("Your mood has been consistently lower recently.")
            recommendations.append("Consider speaking with a counselor or trusted friend about how you're feeling.")
            
        if avg_stress > 3.5:
            insights.append("Stress levels have been elevated lately.")
            recommendations.append("Try incorporating daily stress-reduction activities like deep breathing or short walks.")
            
        if avg_energy < 2.5:
            insights.append("Energy levels have been consistently low.")
            recommendations.append("Focus on sleep quality and consider gentle physical activity to boost energy.")
            
        # Positive insights
        if profile.daily_check_in_streak >= 7:
            insights.append(f"You've maintained a {profile.daily_check_in_streak}-day check-in streak!")
            
        if avg_mood > 4.0:
            insights.append("You've been maintaining positive moods consistently.")
    
    # Get personalized coping strategies
    user_coping = CopingStrategy.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-effectiveness_rating')[:3]
    
    coping_strategies = []
    for strategy in user_coping:
        coping_strategies.append({
            'title': strategy.title,
            'description': strategy.description,
            'category': strategy.category,
            'effectiveness': strategy.effectiveness_rating,
            'times_used': strategy.times_used
        })
    
    return JsonResponse({
        "wellness_score": round(profile.wellness_score, 1),
        "streak": profile.daily_check_in_streak,
        "insights": insights,
        "recommendations": recommendations,
        "coping_strategies": coping_strategies,
        "total_conversations": profile.total_conversations,
        "total_messages": profile.total_messages_sent
    })

@csrf_exempt
@login_required
def submit_feedback_api(request):
    """Allow users to provide feedback on bot responses"""
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        rating = data.get('rating')
        feedback_text = data.get('feedback', '').strip()
        
        if not message_id or not rating:
            return JsonResponse({"error": "Message ID and rating required"}, status=400)
        
        if rating not in range(1, 6):
            return JsonResponse({"error": "Rating must be 1-5"}, status=400)
        
        try:
            message = ChatMessage.objects.get(id=message_id, user=request.user)
        except ChatMessage.DoesNotExist:
            return JsonResponse({"error": "Message not found"}, status=404)
        
        feedback = UserFeedback.objects.create(
            user=request.user,
            message=message,
            rating=rating,
            feedback_text=feedback_text[:500],
            improvement_suggestion=data.get('suggestion', '').strip()[:500]
        )
        
        logger.info(f"Received feedback from user {request.user.id}: {rating} stars")
        
        return JsonResponse({
            "status": "submitted",
            "message": "Thank you for your feedback! It helps me improve."
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        return JsonResponse({"error": "An internal error occurred"}, status=500)

@login_required
def start_new_session_api(request):
    """Start a new conversation session"""
    try:
        # Mark current active session as ended
        ConversationSession.objects.filter(
            user=request.user,
            is_active=True
        ).update(
            is_active=False,
            end_time=timezone.now()
        )
        
        # Create new session
        new_session = ConversationSession.objects.create(
            user=request.user,
            session_id=uuid.uuid4(),
            start_time=timezone.now(),
            is_active=True
        )
        
        return JsonResponse({
            "status": "created",
            "session_id": str(new_session.session_id),
            "message": "New conversation started! How can I help you today?"
        })
        
    except Exception as e:
        logger.error(f"Error creating new session: {e}", exc_info=True)
        return JsonResponse({"error": "Failed to create new session"}, status=500)