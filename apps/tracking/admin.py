from django.contrib import admin

from apps.tracking.models import Message, Mood, Relative, Suggestion


@admin.register(Relative)
class RelativeAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone_number", "is_app_user")
    list_filter = ("is_app_user",)
    search_fields = ("name", "email", "phone_number")


class SuggestionAdmin(admin.StackedInline):
    model = Suggestion
    extra = 1


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ("name", "score", "calculate_brain_health")
    inlines = [SuggestionAdmin]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("message_text", "mood", "is_urgent")
    list_filter = ("is_urgent",)