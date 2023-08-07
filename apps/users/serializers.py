from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.models import Appointment, Feedback, Notification, Therapist, UserHistory

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    therapist = serializers.StringRelatedField(read_only=True)
    appointment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Feedback
        fields = "__all__"


class TherapistProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Therapist
        fields = (
            "degrees",
            "certifications",
            "card_id",
            "hourly_rate",
            "is_available",
        )
        extra_kwargs = {
            "degrees": {"required": False},
            "certifications": {"required": False},
            "card_id": {"required": False},
            "hourly_rate": {"required": False},
            "is_available": {"required": False},
        }


class UserHistorySerializer(serializers.ModelSerializer):
    appointment = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    therapist = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = UserHistory
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="user-detail", lookup_field="id")
    create_feedback = serializers.HyperlinkedIdentityField(
        view_name="users:api-feedback", lookup_field="pk", read_only=True
    )
    create_appointment = serializers.HyperlinkedIdentityField(
        view_name="users:api-create-appointment", lookup_field="pk", read_only=True
    )
    therapist_profile = TherapistProfileSerializer(required=False)
    feedback_therapist = FeedbackSerializer(many=True, read_only=True)
    feedbacks = FeedbackSerializer(many=True, read_only=True)
    therapist_history = UserHistorySerializer(many=True, read_only=True)
    user_history = UserHistorySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "url",
            "name",
            "email",
            "profile_picture",
            "phone_number",
            "date_of_birth",
            "create_feedback",
            "create_appointment",
            "user_history",
            "therapist_history",
            "therapist_profile",
            "feedback_therapist",
            "feedbacks",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not instance.is_therapist:
            fields_to_exclude = [
                "create_feedback",
                "create_appointment",
                "feedback_therapist",
                "therapist_profile",
                "therapist_history",
            ]
        else:
            fields_to_exclude = ["user_history", "feedbacks"]

        data = {key: value for key,
                value in data.items() if key not in fields_to_exclude}
        return data

    def update(self, instance, validated_data):
        therapist_profile_data = validated_data.pop("therapist_profile", None)
        instance = super().update(instance, validated_data)

        if therapist_profile_data and instance.is_therapist:
            therapist_profile_serializer = self.fields["therapist_profile"]
            therapist_profile_instance = instance.therapist_profile

            therapist_profile_serializer.update(
                therapist_profile_instance, therapist_profile_data)

        return instance


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "recipient", "verb", "created_at", "read")


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "email", "password",
                  "brain_health_score", "phone_number", "is_therapist"]

    def create(self, validated_data):
        email = validated_data.get("email")
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(**validated_data)
            return user
        else:
            raise serializers.ValidationError("Email already exists.")


class UserAppointmentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="users:appointment-detail", lookup_field="pk")
    therapist = serializers.ReadOnlyField(source="therapist.user.name")

    class Meta:
        model = Appointment
        fields = ["id", "url", "therapist", "date",
                  "time", "location", "reason", "created_at"]


class TherapistAppointmentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="users:appointment-detail", lookup_field="pk")
    user = serializers.ReadOnlyField(source="user.name")
    date = serializers.ReadOnlyField()
    time = serializers.ReadOnlyField()
    location = serializers.ReadOnlyField()
    reason = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = ["id", "url", "user", "date", "time",
                  "location", "reason", "status", "created_at"]
