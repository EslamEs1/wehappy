from apps.tracking.views import (
    RelativeList,
    MoodListView,
    SuggestionByMoodView,
    RelativeViewSet
    )

from django.urls import path, include
from rest_framework.routers import DefaultRouter


app_name = "truck"
router = DefaultRouter()
router.register(r'relatives', RelativeViewSet)
urlpatterns = [
               
    path('', include(router.urls)),

    path('relatives/', RelativeList.as_view({'get': 'list', 'post': 'create'}), name='relatives-list'),
    path('relatives/<int:pk>/', RelativeList.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='relatives-detail'),
    path('moods/', MoodListView.as_view(), name='mood-list'),
    path('suggestions/by-mood/', SuggestionByMoodView.as_view(), name='suggestion-by-mood'),
    path('check_user/', RelativeList.as_view({'post': 'check_user'}), name='check_user'),

]


