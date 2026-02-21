"""
URL configuration for django-smartbase-admin.
This module is imported lazily to ensure all models are registered first.
"""

from django_smartbase_admin.admin.site import sb_admin_site

from studyfile.assignments.models import Assignment
from studyfile.assignments.models import Submission
from studyfile.assignments.sbadmin import AssignmentAdmin
from studyfile.assignments.sbadmin import SubmissionAdmin
from studyfile.users.models import StudyGroup
from studyfile.users.models import Subject
from studyfile.users.models import TeacherSubject
from studyfile.users.models import User

# Import admin classes
from studyfile.users.sbadmin import StudyGroupAdmin
from studyfile.users.sbadmin import SubjectAdmin
from studyfile.users.sbadmin import TeacherSubjectAdmin
from studyfile.users.sbadmin import UserAdmin

# Register all models
sb_admin_site.register(StudyGroup, StudyGroupAdmin)
sb_admin_site.register(Subject, SubjectAdmin)
sb_admin_site.register(TeacherSubject, TeacherSubjectAdmin)
sb_admin_site.register(User, UserAdmin)
sb_admin_site.register(Assignment, AssignmentAdmin)
sb_admin_site.register(Submission, SubmissionAdmin)

# sb_admin_site.urls returns a tuple (url_patterns, app_name, namespace)
# Unpack all three elements to preserve namespace
urlpatterns, app_name, namespace = sb_admin_site.urls
