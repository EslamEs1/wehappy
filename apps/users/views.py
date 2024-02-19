from decimal import Decimal
import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.db.models import Avg
from django.shortcuts import render



from apps.users.models import Appointment, Brain_Health_Score, Notification, UserHistory
from .serializers import (
    FeedbackSerializer,
    NotificationSerializer,
    TherapistAppointmentSerializer,
    UserAppointmentSerializer,
    UserHistorySerializer,
    UserSerializer,
    UserSignupSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY

User = get_user_model()


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            
            # Fetch the average brain health score
            average_brain_health_score = Brain_Health_Score.objects.aggregate(avg_score=Avg('rating'))['avg_score']
            
            # Set average brain health score to 100 if it's null
            if average_brain_health_score is None:
                average_brain_health_score = 100

            # Create the response data
            user_data = {
                'token': token.key,
                'user_id': user.id,
                'user_name': user.name,
                'average_brain_health_score': average_brain_health_score
            }
            return Response(user_data)
        else:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful.'})


class SignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            username = serializer.validated_data['name']
            password = serializer.validated_data['password']
            phone_number = serializer.validated_data['phone_number']
            is_therapist = serializer.validated_data['is_therapist']
            if not User.objects.filter(name=username).exists():
                user = User.objects.create_user(
                    name=username, password=password, email=email, phone_number=phone_number, is_therapist=is_therapist)
                return Response({'message': 'Signup successful.'})
            else:
                return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(RetrieveModelMixin, ListModelMixin, DestroyModelMixin, UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class TherapistListViewSet(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_therapist=True, is_active=True)
    
class TherapistProfileViewSet(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        try:
            therapist_id = self.kwargs['pk']
            therapist = self.queryset.get(id=therapist_id, is_therapist=True, is_active=True)
            serializer = self.get_serializer(therapist)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'Therapist not found'}, status=status.HTTP_404_NOT_FOUND)


class AppointmentViewSet(RetrieveModelMixin, ListModelMixin, DestroyModelMixin, UpdateModelMixin, viewsets.GenericViewSet):
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


def landing_page(request):
    return render(request, 'home.html')