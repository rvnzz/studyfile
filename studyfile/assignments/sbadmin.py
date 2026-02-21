from django_smartbase_admin.admin.admin_base import SBAdmin


class AssignmentAdmin(SBAdmin):
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
    sbadmin_fieldsets = [
        (
            None,
            {
                "fields": [
                    "title",
                    "description",
                    "subject",
                    "teacher",
                    "due_date",
                    "is_active",
                ],
            },
        ),
    ]


class SubmissionAdmin(SBAdmin):
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
    readonly_fields = ["submitted_at"]
    sbadmin_fieldsets = [
        (
            None,
            {
                "fields": [
                    "student",
                    "assignment",
                    "file",
                    "comment",
                    "status",
                    "grade",
                    "teacher_comment",
                ],
            },
        ),
    ]
