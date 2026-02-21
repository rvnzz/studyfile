from django_smartbase_admin.engine.configuration import SBAdminConfigurationBase
from django_smartbase_admin.engine.configuration import SBAdminRoleConfiguration
from django_smartbase_admin.engine.menu_item import SBAdminMenuItem
from django_smartbase_admin.views.dashboard_view import SBAdminDashboardView

config = SBAdminRoleConfiguration(
    default_view=SBAdminMenuItem(view_id="dashboard"),
    menu_items=[
        SBAdminMenuItem(view_id="dashboard", icon="All-application"),
        # Users menu section
        SBAdminMenuItem(view_id="users_user", icon="User", label="Users"),
        SBAdminMenuItem(view_id="users_studygroup", icon="Users", label="Study Groups"),
        SBAdminMenuItem(view_id="users_subject", icon="Book", label="Subjects"),
        SBAdminMenuItem(
            view_id="users_teachersubject",
            icon="User-check",
            label="Teacher Subjects",
        ),
        # Assignments menu section
        SBAdminMenuItem(
            view_id="assignments_assignment",
            icon="File-text",
            label="Assignments",
        ),
        SBAdminMenuItem(
            view_id="assignments_submission",
            icon="Check-circle",
            label="Submissions",
        ),
    ],
    registered_views=[
        SBAdminDashboardView(widgets=[], title="Dashboard"),
    ],
)


class SBAdminConfiguration(SBAdminConfigurationBase):
    def get_configuration_for_roles(self, user_roles):
        return config
