from django_smartbase_admin.admin.admin_base import SBAdmin


class StudyGroupAdmin(SBAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]
    ordering = ["name"]
    sbadmin_fieldsets = [
        (None, {"fields": ["name"]}),
    ]


class SubjectAdmin(SBAdmin):
    list_display = ["name", "code", "study_group", "created_at"]
    list_filter = ["study_group"]
    search_fields = ["name", "code"]
    ordering = ["study_group", "name"]
    sbadmin_fieldsets = [
        (None, {"fields": ["name", "code", "study_group"]}),
    ]


class TeacherSubjectAdmin(SBAdmin):
    list_display = ["teacher", "subject", "assigned_at"]
    list_filter = ["subject"]
    search_fields = ["teacher__username", "teacher__name", "subject__name"]
    ordering = ["teacher", "subject"]
    sbadmin_fieldsets = [
        (None, {"fields": ["teacher", "subject"]}),
    ]


class UserAdmin(SBAdmin):
    list_display = [
        "username",
        "name",
        "role",
        "study_group",
        "is_approved",
        "is_staff",
    ]
    list_filter = ["role", "is_approved", "is_staff", "study_group"]
    search_fields = ["name", "username", "email"]
    raw_id_fields = ["study_group"]
    sbadmin_fieldsets = [
        (
            None,
            {
                "fields": [
                    "username",
                    "name",
                    "email",
                    "role",
                    "study_group",
                    "is_approved",
                    "is_staff",
                    "is_superuser",
                ],
            },
        ),
    ]
