from django.urls import path
from . import views

urlpatterns = [
    path('', views.journal_list, name='journal_list'),
    path('new/', views.journal_create, name='journal_create'),
    path('<int:pk>/edit/', views.journal_edit, name='journal_edit'),
    path('<int:pk>/delete/', views.journal_delete, name='journal_delete'),
]
