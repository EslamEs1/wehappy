from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status, views, viewsets
from rest_framework.response import Response

from apps.tracking.models import Message, Mood, Relative, Suggestion
from apps.users.models import Brain_Health_Score, Send_To_Relative, Suggestion_Therapist, Therapist

from .serializers import MoodSerializer, RelativeSerializer, SuggestionSerializer


class RelativeList(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RelativeSerializer
    queryset = Relative.objects.all()
    permission_class = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Relative.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MoodListView(generics.ListAPIView):
    serializer_class = MoodSerializer
    queryset = Mood.objects.all()
    permission_class = [permissions.IsAuthenticated]


class SuggestionByMoodView(views.APIView):
    serializer_class = SuggestionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        mood_name = request.query_params.get("mood", "").lower()
        mood = get_object_or_404(Mood, name__iexact=mood_name)

        suggestion = Suggestion.objects.filter(mood=mood).order_by("?").first()
        if not suggestion:
            return Response([], status=status.HTTP_204_NO_CONTENT)

        user = request.user
        Brain_Health_Score.objects.create(user=user, rating=mood.score)

        message = Message.objects.filter(mood=mood).order_by("?").first()
        if message:
            suggestion_text = suggestion.suggestion_text
            message_text = message.message_text
            is_urgent = message.is_urgent
            relatives = user.relative.distinct("name", "email")
            for relative in relatives:
                message_body = (
                    f"Hey {relative.name}, {user.name} has been feeling {mood.name}.\n\n"
                    f"Here's a suggestion: {suggestion_text}\n\n{message_text}\n\n"
                    f"Is urgent: {is_urgent}\n\nThanks,"
                )
                msg = f"{message_body} to {[relative.email]} from 'brainhealth@gmail.com'"
                Send_To_Relative.objects.create(message_text=msg)

        brain_health_score = user.brain_health_score()
        if brain_health_score < 50:
            therapists = Therapist.objects.filter(is_available=True)
            therapists_details = "\n\n".join(
                f"{therapist.user.name}: {therapist.user.email}" for therapist in therapists
            )
            message_body = (
                f"Hey {user.name}, we see your mood is less than 50%, so we suggest "
                f"that you meet with one of the following therapists for brain health therapy:\n\n"
                f"{therapists_details}\n\nThanks"
            )
            Suggestion_Therapist.objects.create(message_text=message_body)

        serializer = self.serializer_class(suggestion)
        return Response(serializer.data, status=status.HTTP_200_OK)