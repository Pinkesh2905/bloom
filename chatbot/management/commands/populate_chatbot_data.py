# management/commands/populate_chatbot_data.py
# Create this file in: chatbot/management/commands/populate_chatbot_data.py

from django.core.management.base import BaseCommand
from chatbot.models import (
    BotPersonality, MotivationalQuote, Joke, Affirmation, 
    Achievement, CrisisResource
)

class Command(BaseCommand):
    help = 'Populate the chatbot with initial sample data'
    
    def handle(self, *args, **options):
        self.stdout.write('Populating chatbot with sample data...')
        
        # Create default bot personality
        self.create_bot_personalities()
        
        # Add motivational quotes
        self.create_motivational_quotes()
        
        # Add jokes
        self.create_jokes()
        
        # Add affirmations
        self.create_affirmations()
        
        # Create achievements
        self.create_achievements()
        
        # Add crisis resources
        self.create_crisis_resources()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated chatbot data!')
        )
    
    def create_bot_personalities(self):
        personalities = [
            {
                'name': 'Bloom (Default)',
                'description': 'Empathetic and supportive wellness companion',
                'is_default': True,
                'empathy_level': 0.9,
                'humor_level': 0.4,
                'formality_level': 0.2,
                'proactivity_level': 0.7,
            },
            {
                'name': 'Sunny',
                'description': 'Cheerful and optimistic personality',
                'is_default': False,
                'empathy_level': 0.8,
                'humor_level': 0.8,
                'formality_level': 0.1,
                'proactivity_level': 0.8,
            },
            {
                'name': 'Calm',
                'description': 'Peaceful and mindful personality',
                'is_default': False,
                'empathy_level': 0.9,
                'humor_level': 0.2,
                'formality_level': 0.3,
                'proactivity_level': 0.5,
            }
        ]
        
        for personality_data in personalities:
            personality, created = BotPersonality.objects.get_or_create(
                name=personality_data['name'],
                defaults=personality_data
            )
            if created:
                self.stdout.write(f'Created personality: {personality.name}')
    
    def create_motivational_quotes(self):
        quotes = [
            {
                'text': "Every day is a new beginning. Take a deep breath, smile, and start again.",
                'author': "Unknown",
                'category': "motivation",
                'mood_context': ["terrible", "bad", "okay"]
            },
            {
                'text': "The only way to do great work is to love what you do.",
                'author': "Steve Jobs",
                'category': "inspiration",
                'mood_context': ["okay", "good"]
            },
            {
                'text': "Believe you can and you're halfway there.",
                'author': "Theodore Roosevelt",
                'category': "confidence",
                'mood_context': ["bad", "okay", "good"]
            },
            {
                'text': "Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.",
                'author': "Unknown",
                'category': "wellness",
                'mood_context': ["terrible", "bad", "okay"]
            },
            {
                'text': "Progress, not perfection, is the goal.",
                'author': "Unknown",
                'category': "growth",
                'mood_context': ["okay", "good", "great"]
            },
            {
                'text': "You are stronger than you think, braver than you feel, and more loved than you know.",
                'author': "Unknown",
                'category': "strength",
                'mood_context': ["terrible", "bad"]
            },
            {
                'text': "Happiness can be found even in the darkest of times, if one only remembers to turn on the light.",
                'author': "Albus Dumbledore",
                'category': "hope",
                'mood_context': ["terrible", "bad", "okay"]
            },
            {
                'text': "The present moment is the only time over which we have dominion.",
                'author': "Thich Nhat Hanh",
                'category': "mindfulness",
                'mood_context': ["okay", "good", "great"]
            }
        ]
        
        for quote_data in quotes:
            quote, created = MotivationalQuote.objects.get_or_create(
                text=quote_data['text'],
                defaults=quote_data
            )
            if created:
                self.stdout.write(f'Created quote by {quote.author}')
    
    def create_jokes(self):
        jokes = [
            {
                'text': "Why don't scientists trust atoms? Because they make up everything!",
                'category': "science",
                'appropriateness_level': "family"
            },
            {
                'text': "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                'category': "puns",
                'appropriateness_level': "family"
            },
            {
                'text': "Why did the scarecrow win an award? He was outstanding in his field!",
                'category': "puns",
                'appropriateness_level': "family"
            },
            {
                'text': "What do you call a fake noodle? An impasta!",
                'category': "food",
                'appropriateness_level': "family"
            },
            {
                'text': "Why don't eggs tell jokes? They'd crack each other up!",
                'category': "food",
                'appropriateness_level': "family"
            },
            {
                'text': "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
                'category': "geography",
                'appropriateness_level': "family"
            },
            {
                'text': "I'm reading a book about anti-gravity. It's impossible to put down!",
                'category': "science",
                'appropriateness_level': "family"
            },
            {
                'text': "Why did the math book look so sad? Because it was full of problems!",
                'category': "education",
                'appropriateness_level': "family"
            }
        ]
        
        for joke_data in jokes:
            joke, created = Joke.objects.get_or_create(
                text=joke_data['text'],
                defaults=joke_data
            )
            if created:
                self.stdout.write(f'Created joke: {joke.text[:50]}...')
    
    def create_affirmations(self):
        affirmations = [
            {
                'text': "I am worthy of love and respect, starting with my own.",
                'category': "self-love",
                'target_emotion': ["depression", "anxiety"]
            },
            {
                'text': "I choose to focus on what I can control and let go of what I cannot.",
                'category': "control",
                'target_emotion': ["anxiety", "anger"]
            },
            {
                'text': "Every breath I take fills me with calm and peace.",
                'category': "breathing",
                'target_emotion': ["anxiety", "stress"]
            },
            {
                'text': "I am grateful for this moment and all the possibilities it holds.",
                'category': "gratitude",
                'target_emotion': ["depression", "sadness"]
            },
            {
                'text': "I have overcome challenges before, and I will overcome this one too.",
                'category': "strength",
                'target_emotion': ["fear", "anxiety"]
            },
            {
                'text': "My feelings are valid, and it's okay to experience them fully.",
                'category': "validation",
                'target_emotion': ["sadness", "guilt"]
            },
            {
                'text': "I am learning and growing every day, and that's enough.",
                'category': "growth",
                'target_emotion': ["perfectionism", "self-doubt"]
            },
            {
                'text': "I deserve kindness, especially from myself.",
                'category': "self-compassion",
                'target_emotion': ["self-criticism", "depression"]
            },
            {
                'text': "This difficult moment will pass, and I will be okay.",
                'category': "resilience",
                'target_emotion': ["despair", "overwhelm"]
            },
            {
                'text': "I trust in my ability to handle whatever comes my way.",
                'category': "confidence",
                'target_emotion': ["fear", "anxiety"]
            }
        ]
        
        for affirmation_data in affirmations:
            affirmation, created = Affirmation.objects.get_or_create(
                text=affirmation_data['text'],
                defaults=affirmation_data
            )
            if created:
                self.stdout.write(f'Created affirmation: {affirmation.text[:50]}...')
    
    def create_achievements(self):
        achievements = [
            # Streak Achievements
            {
                'name': 'First Steps',
                'description': 'Complete your first daily check-in',
                'icon': '🌱',
                'achievement_type': 'streak',
                'rarity': 'common',
                'requirement_value': 1,
                'points': 10
            },
            {
                'name': 'Getting Started',
                'description': 'Maintain a 3-day check-in streak',
                'icon': '🌿',
                'achievement_type': 'streak',
                'rarity': 'common',
                'requirement_value': 3,
                'points': 25
            },
            {
                'name': 'Week Warrior',
                'description': 'Maintain a 7-day check-in streak',
                'icon': '⭐',
                'achievement_type': 'streak',
                'rarity': 'rare',
                'requirement_value': 7,
                'points': 50
            },
            {
                'name': 'Two Week Champion',
                'description': 'Maintain a 14-day check-in streak',
                'icon': '🏆',
                'achievement_type': 'streak',
                'rarity': 'rare',
                'requirement_value': 14,
                'points': 100
            },
            {
                'name': 'Monthly Master',
                'description': 'Maintain a 30-day check-in streak',
                'icon': '💎',
                'achievement_type': 'streak',
                'rarity': 'epic',
                'requirement_value': 30,
                'points': 200
            },
            {
                'name': 'Consistency Legend',
                'description': 'Maintain a 100-day check-in streak',
                'icon': '👑',
                'achievement_type': 'streak',
                'rarity': 'legendary',
                'requirement_value': 100,
                'points': 500
            },
            
            # Conversation Achievements
            {
                'name': 'Chatty',
                'description': 'Have your first conversation with Bloom',
                'icon': '💬',
                'achievement_type': 'conversation',
                'rarity': 'common',
                'requirement_value': 1,
                'points': 10
            },
            {
                'name': 'Social Butterfly',
                'description': 'Have 10 conversations with Bloom',
                'icon': '🦋',
                'achievement_type': 'conversation',
                'rarity': 'common',
                'requirement_value': 10,
                'points': 50
            },
            {
                'name': 'Deep Thinker',
                'description': 'Have 50 conversations with Bloom',
                'icon': '🧠',
                'achievement_type': 'conversation',
                'rarity': 'rare',
                'requirement_value': 50,
                'points': 150
            },
            {
                'name': 'Wisdom Seeker',
                'description': 'Have 100 conversations with Bloom',
                'icon': '🦉',
                'achievement_type': 'conversation',
                'rarity': 'epic',
                'requirement_value': 100,
                'points': 300
            },
            
            # Gratitude Achievements
            {
                'name': 'Grateful Heart',
                'description': 'Practice gratitude for the first time',
                'icon': '🙏',
                'achievement_type': 'gratitude',
                'rarity': 'common',
                'requirement_value': 1,
                'points': 15
            },
            {
                'name': 'Thankful Soul',
                'description': 'Practice gratitude 10 times',
                'icon': '✨',
                'achievement_type': 'gratitude',
                'rarity': 'rare',
                'requirement_value': 10,
                'points': 75
            },
            {
                'name': 'Gratitude Guru',
                'description': 'Practice gratitude 50 times',
                'icon': '🌟',
                'achievement_type': 'gratitude',
                'rarity': 'epic',
                'requirement_value': 50,
                'points': 250
            },
            
            # Engagement Achievements
            {
                'name': 'Marathon Chatter',
                'description': 'Have a conversation with 20+ messages',
                'icon': '🏃',
                'achievement_type': 'engagement',
                'rarity': 'rare',
                'requirement_string': 'long_conversation',
                'points': 100
            },
            {
                'name': 'Wellness Warrior',
                'description': 'Achieve 75% wellness score',
                'icon': '⚡',
                'achievement_type': 'wellness',
                'rarity': 'epic',
                'requirement_value': 75,
                'points': 200
            },
            {
                'name': 'Mindfulness Master',
                'description': 'Complete 25 mindfulness exercises',
                'icon': '🧘',
                'achievement_type': 'mindfulness',
                'rarity': 'epic',
                'requirement_value': 25,
                'points': 175
            }
        ]
        
        for achievement_data in achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )
            if created:
                self.stdout.write(f'Created achievement: {achievement.name}')
    
    def create_crisis_resources(self):
        crisis_resources = [
            {
                'name': 'National Suicide Prevention Lifeline',
                'phone_number': '988',
                'website': 'https://suicidepreventionlifeline.org/',
                'description': '24/7 suicide prevention and crisis support',
                'country': 'US',
                'availability': '24/7',
                'specialization': ['suicide', 'crisis', 'depression'],
                'priority_order': 1
            },
            {
                'name': 'Crisis Text Line',
                'phone_number': 'Text HOME to 741741',
                'website': 'https://www.crisistextline.org/',
                'description': '24/7 crisis support via text message',
                'country': 'US',
                'availability': '24/7',
                'specialization': ['crisis', 'text', 'youth'],
                'priority_order': 2
            },
            {
                'name': 'National Alliance on Mental Illness',
                'phone_number': '1-800-950-6264',
                'website': 'https://www.nami.org/',
                'description': 'Mental health support and information',
                'country': 'US',
                'availability': 'Mon-Fri 10am-10pm ET',
                'specialization': ['mental health', 'support', 'information'],
                'priority_order': 3
            },
            {
                'name': 'SAMHSA National Helpline',
                'phone_number': '1-800-662-4357',
                'website': 'https://www.samhsa.gov/find-help/national-helpline',
                'description': 'Substance abuse and mental health services',
                'country': 'US',
                'availability': '24/7',
                'specialization': ['substance abuse', 'mental health', 'treatment'],
                'priority_order': 4
            },
            {
                'name': 'National Domestic Violence Hotline',
                'phone_number': '1-800-799-7233',
                'website': 'https://www.thehotline.org/',
                'description': '24/7 domestic violence support',
                'country': 'US',
                'availability': '24/7',
                'specialization': ['domestic violence', 'abuse', 'safety'],
                'priority_order': 5
            },
            {
                'name': 'Trans Lifeline',
                'phone_number': '877-565-8860',
                'website': 'https://translifeline.org/',
                'description': 'Crisis support for transgender individuals',
                'country': 'US',
                'availability': '24/7',
                'specialization': ['transgender', 'LGBTQ+', 'crisis'],
                'priority_order': 6
            }
        ]
        
        for resource_data in crisis_resources:
            resource, created = CrisisResource.objects.get_or_create(
                name=resource_data['name'],
                defaults=resource_data
            )
            if created:
                self.stdout.write(f'Created crisis resource: {resource.name}')
        
        self.stdout.write(
            self.style.WARNING(
                'Note: Crisis resources are set for US. Please update with local resources for your region.'
            )
        )