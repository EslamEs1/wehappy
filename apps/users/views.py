from decimal import Decimal
import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework import generics, status
from django.contrib.auth import authenticate, login

from apps.users.models import Appointment, Notification, UserHistory
from .serializers import (
    FeedbackSerializer,
    NotificationSerializer,
    TherapistAppointmentSerializer,
    UserAppointmentSerializer,
    UserHistorySerializer,
    UserSerializer,
    LoginSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY

User = get_user_model()


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the email and password from the serializer data
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Authenticate the user using Django's built-in authenticate method
        user = authenticate(request, username=email, password=password)

        # If the user is not authenticated, return an error response
        if user is None:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Log the user in by creating a session
        login(request, user)

        # You can perform additional actions here if needed before returning the response.

        return Response({'detail': 'Login successful.'})


class TherapistListViewSet(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_therapist=True, is_active=True)


class AppointmentViewSet(RetrieveModelMixin, ListModelMixin, DestroyModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Appointment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_therapist:
            therapist = user
            return Appointment.objects.filter(therapist=therapist)
        else:
            return Appointment.objects.filter(user=user)

    def get_serializer_class(self):
        if not self.request.user.is_therapist:
            return UserAppointmentSerializer
        else:
            return TherapistAppointmentSerializer

    def perform_update(self, serializer):
        instance = serializer.instance
        if self.request.user.is_therapist:
            status = serializer.validated_data.get("status")
            if status in ["completed", "cancelled"]:
                if status == "cancelled":
                    # Calculate the refund amount (80%)
                    total_amount = instance.hourly_rate * instance.duration
                    refund_amount = total_amount * Decimal("0.8")
                    # Charge 20% as cancellation fee
                    cancellation_fee = total_amount * Decimal("0.2")
                    # Perform refund and charge operations with Stripe
                    stripe.Refund.create(
                        payment_intent=instance.payment_intent_id,
                        amount=int(refund_amount * 100),  # Convert to cents
                    )
                    stripe.Charge.create(
                        amount=int(cancellation_fee * 100),  # Convert to cents
                        currency="usd",
                        customer=instance.customer_id,
                        description="Cancellation fee",
                    )

                if status == "completed":
                    # Calculate the charge amount (including 10% additional fee)
                    total_amount = instance.hourly_rate * instance.duration
                    charge_amount = total_amount * Decimal("1.1")
                    # Perform charge operation with Stripe
                    stripe.Charge.create(
                        amount=int(charge_amount * 100),  # Convert to cents
                        currency="usd",
                        customer=instance.customer_id,
                        description="Appointment charge",
                    )
        serializer.save()


class CreateAppointmentViewSet(CreateAPIView):
    serializer_class = UserAppointmentSerializer
    queryset = Appointment.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        therapist_id = self.kwargs.get("pk")
        therapist = User.objects.get(pk=therapist_id)
        serializer.save(user=user, therapist=therapist)


class FeedbackCreateView(CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        therapist_id = self.kwargs.get("pk")
        therapist = User.objects.get(pk=therapist_id)
        appointment_id = self.request.data.get("appointment_id")
        appointment = Appointment.objects.get(pk=appointment_id)

        serializer.save(user=self.request.user,
                        therapist=therapist, appointment=appointment)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(recipient=user)


class UserHistoryListAPIView(ListAPIView):
    queryset = UserHistory.objects.all()
    serializer_class = UserHistorySerializer
