from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    # Assignment URLs
    path("", views.AssignmentListView.as_view(), name="list"),
    path("create/", views.AssignmentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.AssignmentDetailView.as_view(), name="detail"),
    path("<int:pk>/update/", views.AssignmentUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.AssignmentDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/download-submissions/",
        views.AssignmentSubmissionsDownloadView.as_view(),
        name="download_submissions",
    ),
    # Submission URLs
    path(
        "<int:assignment_pk>/submit/",
        views.SubmissionCreateView.as_view(),
        name="submit",
    ),
    path(
        "submissions/",
        views.TeacherSubmissionsListView.as_view(),
        name="submissions",
    ),
    path(
        "submissions/<int:pk>/",
        views.SubmissionDetailView.as_view(),
        name="submission_detail",
    ),
    path(
        "submissions/<int:pk>/grade/",
        views.SubmissionGradeView.as_view(),
        name="submission_grade",
    ),
]
