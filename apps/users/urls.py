from django.urls import path

from apps.users.views import (
    CreateAppointmentViewSet,
    FeedbackCreateView,
    TherapistListViewSet,
    UserHistoryListAPIView,
    AppointmentViewSet,
    NotificationViewSet,
    )

from .webhooks import stripe_webhook

app_name = "users"

urlpatterns = [
    path("therapists/", TherapistListViewSet.as_view(), name="api-therapist"),
    path("feedback/<int:pk>/", FeedbackCreateView.as_view(), name="api-feedback"),
    path("create-appointment/<int:pk>/", CreateAppointmentViewSet.as_view(), name="api-create-appointment"),
    path("user-history/", UserHistoryListAPIView.as_view(), name="api-user-history"),
    
    path('appointment/', AppointmentViewSet.as_view({'get': 'list',}), name='appointment-list'),
    path('appointment/<int:pk>/', AppointmentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='appointment-detail'),
    path('notifications/', NotificationViewSet.as_view({'get': 'list'}), name='notification-list'),
    path('notifications/<int:pk>/', NotificationViewSet.as_view({'get': 'retrieve'}), name='notification-detail'),
    
    
    path("webhook/stripe/", stripe_webhook, name="stripe_webhook"),
]