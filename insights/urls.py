from django.urls import path
from .views import InsightsHomeView

urlpatterns = [
    # The path remains the same, but now points to a Class-Based View
    path('', InsightsHomeView.as_view(), name='insights_home'),
]
