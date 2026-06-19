from django.urls import path

from . import views

app_name = "ai_grading"

urlpatterns = [
    path(
        "submissions/<int:pk>/ai-grade/",
        views.AIGradingTriggerView.as_view(),
        name="trigger",
    ),
    path(
        "submissions/<int:pk>/ai-confirm/",
        views.AIGradingConfirmView.as_view(),
        name="confirm",
    ),
]
