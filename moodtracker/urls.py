from django.urls import path
from . import views

urlpatterns = [
    path('', views.mood_tracker, name='mood_tracker'),
]
