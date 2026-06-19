import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def grade_submission_task(self, submission_id: int):
    from studyfile.assignments.models import Submission

    from .agent import run_grading_agent

    try:
        submission = Submission.objects.select_related("assignment").get(pk=submission_id)
    except Submission.DoesNotExist:
        logger.error("Submission %s not found", submission_id)
        return

    submission.ai_status = Submission.AIStatus.PROCESSING
    submission.save(update_fields=["ai_status"])

    try:
        file_path = submission.file.path

        result = run_grading_agent(
            assignment_title=submission.assignment.title,
            assignment_description=submission.assignment.description,
            submission_file_path=file_path,
            student_comment=submission.comment,
        )

        submission.ai_grade = result.get("grade")
        submission.ai_feedback = result.get("feedback", "")
        submission.ai_status = Submission.AIStatus.COMPLETED
        submission.ai_graded_at = timezone.now()
        submission.save(update_fields=[
            "ai_grade",
            "ai_feedback",
            "ai_status",
            "ai_graded_at",
        ])

        logger.info("AI grading completed for submission %s", submission_id)

    except Exception as exc:
        logger.exception("AI grading failed for submission %s", submission_id)
        submission.ai_status = Submission.AIStatus.FAILED
        submission.ai_feedback = f"Ошибка при проверке: {exc}"
        submission.save(update_fields=["ai_status", "ai_feedback"])

        raise self.retry(exc=exc, countdown=60)
