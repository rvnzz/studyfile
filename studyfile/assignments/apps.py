from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AssignmentsConfig(AppConfig):
    name = "studyfile.assignments"
    verbose_name = _("Assignments")

    def ready(self):
        pass
