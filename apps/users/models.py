from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token

from apps.users.managers import UserManager


class User(AbstractUser):
    name = models.CharField(_("Name of User"), max_length=255, unique=True)
    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to="user_profiles/", null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_therapist = models.BooleanField(default=False)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def brain_health_score(self):
        ratings = self.brain_score.all()
        if ratings:
            return round(sum(r.rating for r in ratings) / len(ratings), 2)
        else:
            return 0

    def star(self):
        ratings = self.feedback_therapist.all()
        if ratings:
            return round(sum(r.rating for r in ratings) / len(ratings), 2)
        else:
            return 0
    

class Therapist(models.Model):
    user = models.OneToOneField(User, related_name="therapist_profile", on_delete=models.CASCADE)
    degrees = models.TextField(null=True, blank=True)
    certifications = models.TextField(null=True, blank=True)
    card_id = models.CharField(max_length=25)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email


@receiver(post_save, sender=User)
def create_therapist_profile(sender, instance, created, **kwargs):
    if created and instance.is_therapist:
        Therapist.objects.create(user=instance)


class Appointment(models.Model):
    user = models.ForeignKey(User, related_name="appointments", on_delete=models.CASCADE)
    therapist = models.ForeignKey(User, related_name="appointment_User", on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    reason = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=(
            ("BOOKED", "Booked"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
            ("CANCELED", "Canceled"),
        ),
        default="BOOKED",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.name} - {self.therapist.name}"


@receiver(post_save, sender=Appointment)
def create_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.therapist,
            verb=f"You have a new appointment with {instance.user.name}",
            created_at=timezone.now(),
        )


@receiver(post_save, sender=Appointment)
def update_notification_status(sender, instance, **kwargs):
    if instance.status == "CANCELED":
        Notification.objects.create(
            recipient=instance.user,
            verb=f"Your appointment with {instance.therapist.name} has been canceled",
            created_at=timezone.now(),
            read=True,
        )


@receiver(post_save, sender=Appointment)
def create_user_history(sender, instance, created, **kwargs):
    if created and instance.status == "BOOKED":
        UserHistory.objects.create(user=instance.user, therapist=instance.therapist, appointment=instance)


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    verb = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.name} - {self.verb}"


class Feedback(models.Model):
    user = models.ForeignKey(User, related_name="feedbacks", on_delete=models.CASCADE)
    therapist = models.ForeignKey(User, related_name="feedback_therapist", on_delete=models.CASCADE)
    appointment = models.OneToOneField(Appointment, related_name="review", on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()

    def __str__(self):
        return f"{self.user.name} - {self.user.email}"


class UserHistory(models.Model):
    user = models.ForeignKey(User, related_name="user_history", on_delete=models.CASCADE)
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name="therapist_history")
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.name} - {self.therapist.name}"


class Brain_Health_Score(models.Model):
    user = models.ForeignKey(User, related_name="brain_score", on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])

    def __str__(self):
        return f"{self.user.name} - {self.rating}"


class Send_To_Relative(models.Model):
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Send To Relative"
        verbose_name_plural = "Send To Relatives"
        ordering = ["-created_at"]

    def __str__(self):
        return self.message_text


class Suggestion_Therapist(models.Model):
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suggestion Therapist"
        verbose_name_plural = "Suggestion Therapists"
        ordering = ["-created_at"]

    def __str__(self):
        return self.message_text