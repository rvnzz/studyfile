from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from studyfile.users.models import Subject
from studyfile.users.models import User


class Assignment(models.Model):
    """Assignment created by teachers for students."""

    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Subject"),
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_assignments",
        verbose_name=_("Teacher"),
        limit_choices_to={"role": "teacher"},
    )
    due_date = models.DateTimeField(_("Due Date"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Assignment")
        verbose_name_plural = _("Assignments")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.subject.name})"

    def get_absolute_url(self) -> str:
        return reverse("assignments:detail", kwargs={"pk": self.pk})

    @property
    def target_group(self):
        """Returns the study group this assignment is for (via subject)."""
        return self.subject.study_group


class Submission(models.Model):
    """Student submission for an assignment."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", _("Submitted")
        GRADED = "graded", _("Graded")
        RETURNED = "returned", _("Returned")

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name=_("Assignment"),
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name=_("Student"),
        limit_choices_to={"role": "student"},
    )
    file = models.FileField(
        _("File"),
        upload_to="submissions/%Y/%m/%d/",
        help_text=_("Upload your assignment file"),
    )
    comment = models.TextField(
        _("Comment"),
        blank=True,
        help_text=_("Optional comment about your submission"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    grade = models.DecimalField(
        _("Grade"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    teacher_comment = models.TextField(
        _("Teacher Comment"),
        blank=True,
        help_text=_("Teacher's feedback on the submission"),
    )
    submitted_at = models.DateTimeField(_("Submitted At"), auto_now_add=True)
    graded_at = models.DateTimeField(_("Graded At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Submission")
        verbose_name_plural = _("Submissions")
        ordering = ["-submitted_at"]
        unique_together = ["assignment", "student"]

    def __str__(self) -> str:
        return f"{self.student.username} - {self.assignment.title}"

    def get_absolute_url(self) -> str:
        return reverse("assignments:submission_detail", kwargs={"pk": self.pk})
