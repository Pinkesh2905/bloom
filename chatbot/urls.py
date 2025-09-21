from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Main chatbot interface
    path('', views.chatbot_view, name='chatbot_home'),
    
    # Core chat functionality (API)
    path('api/send/', views.send_message, name='send_message'),
    path('api/session/new/', views.start_new_session_api, name='start_new_session'),
    path('api/history/sessions/', views.get_session_history_api, name='get_session_history'),
    path('api/history/chat/', views.get_chat_history_api, name='get_chat_history'),
    path('api/clear/', views.clear_chat_history_api, name='clear_chat'),
    
    # Mood tracking endpoints (API)
    path('api/mood/save/', views.save_mood_entry_api, name='save_mood'),
    path('api/mood/patterns/', views.get_mood_patterns_api, name='mood_patterns'),
    
    # Wellness and analytics (API)
    path('api/wellness/insights/', views.get_wellness_insights_api, name='wellness_insights'),
    path('api/achievements/', views.get_achievements_api, name='get_achievements'),
    
    # User feedback (API)
    path('api/feedback/', views.submit_feedback_api, name='submit_feedback'),
]