from django.urls import path
from . import views

urlpatterns = [
    path('', views.JournalListView.as_view(), name='journal_list'),
    path('create/', views.JournalCreateView.as_view(), name='journal_create'),
    path('<int:pk>/', views.JournalDetailView.as_view(), name='journal_detail'),
    path('<int:pk>/edit/', views.JournalUpdateView.as_view(), name='journal_edit'),
    path('<int:pk>/delete/', views.JournalDeleteView.as_view(), name='journal_delete'),
    path('analytics/', views.MoodAnalyticsView.as_view(), name='mood_analytics'),
    # path('tag/<str:tag_name>/', views.TaggedJournalListView.as_view(), name='journal_tagged'),
]
