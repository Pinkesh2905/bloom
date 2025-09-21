from django.urls import path
from . import views

urlpatterns = [
    path('', views.JournalListView.as_view(), name='journal_list'),
    path('entry/<int:pk>/', views.JournalDetailView.as_view(), name='journal_detail'),
    path('new/', views.JournalCreateView.as_view(), name='journal_create'),
    path('entry/<int:pk>/edit/', views.JournalUpdateView.as_view(), name='journal_edit'),
    path('entry/<int:pk>/delete/', views.JournalDeleteView.as_view(), name='journal_delete'),
    # path('tag/<str:tag_name>/', views.TaggedJournalListView.as_view(), name='journal_tagged'),
]
