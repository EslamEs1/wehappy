from django.urls import path
from apps.users.views import (
    CreateAppointmentViewSet,
    FeedbackCreateView,
    TherapistListViewSet,
    TherapistProfileViewSet,
    UserHistoryListAPIView,
    AppointmentViewSet,
    NotificationViewSet,
    UserViewSet
)

from .webhooks import stripe_webhook

app_name = "users"


urlpatterns = [
    path('users/',
         UserViewSet.as_view({'get': 'list', }), name='users-list'),
    path('users/<int:pk>/', UserViewSet.as_view(
        {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='users-detail'),

    path("therapists/", TherapistListViewSet.as_view(), name="api-therapist"),
        path("therapists/<int:pk>/", TherapistProfileViewSet.as_view(), name="api-therapist-profile"),

    path("feedback/<int:pk>/", FeedbackCreateView.as_view(), name="api-feedback"),
    path("create-appointment/<int:pk>/",
         CreateAppointmentViewSet.as_view(), name="api-create-appointment"),
    path("user-history/", UserHistoryListAPIView.as_view(), name="api-user-history"),

    path('appointment/',
         AppointmentViewSet.as_view({'get': 'list', }), name='appointment-list'),
    path('appointment/<int:pk>/', AppointmentViewSet.as_view(
        {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='appointment-detail'),
    path('notifications/',
         NotificationViewSet.as_view({'get': 'list'}), name='notification-list'),
    path('notifications/<int:pk>/',
         NotificationViewSet.as_view({'get': 'retrieve'}), name='notification-detail'),


    path("webhook/stripe/", stripe_webhook, name="stripe_webhook"),
]
