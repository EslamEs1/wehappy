from apps.tracking.views import (
    RelativeList,
    MoodListView,
    SuggestionByMoodView,
    )

from django.urls import path


app_name = "truck"

urlpatterns = [
    path('relatives/', RelativeList.as_view({'get': 'list', 'post': 'create'}), name='relatives-list'),
    path('relatives/<int:pk>/', RelativeList.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='relatives-detail'),
    path('moods/', MoodListView.as_view(), name='mood-list'),
    path('suggestions/by-mood/', SuggestionByMoodView.as_view(), name='suggestion-by-mood'),

]


