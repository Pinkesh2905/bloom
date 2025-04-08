from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot_home'),
    path('send/', views.send_message, name='send_message'),
    path('history/', views.get_chat_history, name='get_history'),
    path('clear/', views.clear_chat, name='clear_chat'),
]
