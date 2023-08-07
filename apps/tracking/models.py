from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Relative(models.Model):
    user = models.ForeignKey(User, related_name="relative", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    is_app_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Mood(models.Model):
    name = models.CharField(max_length=100)
    img_emoji = models.ImageField(upload_to="mood/emoji")
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def calculate_brain_health(self):
        max_score = 100  # Maximum possible score
        if self.score is None or self.score <= 0:
            return 0
        elif self.score >= max_score:
            return 100
        else:
            return (self.score / max_score) * 100


class Suggestion(models.Model):
    mood = models.ForeignKey(Mood, related_name="suggestion", on_delete=models.CASCADE)
    suggestion_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.suggestion_text


class Message(models.Model):
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    message_text = models.TextField()
    is_urgent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin Message"
        verbose_name_plural = "Admin Messages"
        ordering = ["-created_at"]

    def __str__(self):
        return self.message_text