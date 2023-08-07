from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.users.forms import UserAdminChangeForm, UserAdminCreationForm

from .models import (
    Appointment,
    Brain_Health_Score,
    Feedback,
    Send_To_Relative,
    Suggestion_Therapist,
    Therapist,
    UserHistory,
)

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "name",
                    "date_of_birth",
                    "is_therapist",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["email", "name", "is_superuser", "is_active", "is_therapist", "brain_health_score"]
    search_fields = ["name"]
    ordering = ["id"]
    list_editable = ["is_active"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


admin.site.register(Brain_Health_Score)


@admin.register(Send_To_Relative)
class Send_To_RelativeAdmin(admin.ModelAdmin):
    pass


@admin.register(Suggestion_Therapist)
class Suggestion_TherapistAdmin(admin.ModelAdmin):
    pass


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass


@admin.register(Feedback)
class FeedBackAdmin(admin.ModelAdmin):
    list_display = ("rating", "comment", "user", "therapist")
    # readonly_fields = ["rating", "comment", "therapist", "user"]


@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    list_display = ("user", "hourly_rate", "is_available")
    list_filter = ("is_available",)


@admin.register(UserHistory)
class UserHistoryAdmin(admin.ModelAdmin):
    pass