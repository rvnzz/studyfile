from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View

from studyfile.assignments.models import Submission
from studyfile.assignments.views import TeacherRequiredMixin


class AIGradingTriggerView(LoginRequiredMixin, TeacherRequiredMixin, View):

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)

        if not request.user.is_admin and submission.assignment.teacher != request.user:
            messages.error(request, "У вас нет разрешения на проверку этой сдачи.")
            return redirect("assignments:submission_detail", pk=pk)

        if submission.ai_status == Submission.AIStatus.PROCESSING:
            messages.warning(request, "Проверка уже запущена.")
            return redirect("assignments:submission_detail", pk=pk)

        from studyfile.ai_grading.tasks import grade_submission_task

        submission.ai_status = Submission.AIStatus.PENDING
        submission.ai_grade = None
        submission.ai_feedback = ""
        submission.ai_graded_at = None
        submission.save(update_fields=[
            "ai_status",
            "ai_grade",
            "ai_feedback",
            "ai_graded_at",
        ])

        grade_submission_task.delay(submission.pk)

        messages.success(request, "AI проверка запущена. Результат появится через некоторое время.")
        return redirect("assignments:submission_detail", pk=pk)


class AIGradingConfirmView(LoginRequiredMixin, TeacherRequiredMixin, View):

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)

        if not request.user.is_admin and submission.assignment.teacher != request.user:
            messages.error(request, "У вас нет разрешения на подтверждение этой оценки.")
            return redirect("assignments:submission_detail", pk=pk)

        if submission.ai_status != Submission.AIStatus.COMPLETED or submission.ai_grade is None:
            messages.error(request, "AI оценка еще не готова.")
            return redirect("assignments:submission_detail", pk=pk)

        submission.grade = submission.ai_grade
        submission.teacher_comment = submission.ai_feedback
        submission.status = Submission.Status.GRADED
        submission.graded_at = timezone.now()
        submission.save(update_fields=[
            "grade",
            "teacher_comment",
            "status",
            "graded_at",
        ])

        messages.success(request, "Оценка AI подтверждена и сохранена.")
        return redirect("assignments:submission_detail", pk=pk)
