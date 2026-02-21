from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Assignment
from .models import Submission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "subject",
        "teacher",
        "due_date",
        "is_active",
        "created_at",
    ]
    list_filter = ["subject__study_group", "is_active", "created_at"]
    search_fields = ["title", "description", "subject__name", "teacher__username"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    autocomplete_fields = ["subject", "teacher"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "assignment", "status", "grade", "submitted_at"]
    list_filter = ["status", "submitted_at", "assignment__subject"]
    search_fields = [
        "student__username",
        "student__name",
        "assignment__title",
        "comment",
        "teacher_comment",
    ]
    ordering = ["-submitted_at"]
    date_hierarchy = "submitted_at"
    autocomplete_fields = ["student", "assignment"]
    readonly_fields = ["submitted_at"]
    fieldsets = (
        (None, {"fields": ("assignment", "student", "file", "status")}),
        (_("Content"), {"fields": ("comment", "grade", "teacher_comment")}),
        (_("Dates"), {"fields": ("submitted_at", "graded_at")}),
    )
