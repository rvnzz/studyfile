from django.db import models
from django.urls import reverse

from studyfile.users.models import Subject
from studyfile.users.models import User


class Assignment(models.Model):
    """Assignment created by teachers for students."""

    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание")
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Предмет",
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_assignments",
        verbose_name="Преподаватель",
        limit_choices_to={"role": "teacher"},
    )
    due_date = models.DateTimeField("Срок сдачи", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    is_active = models.BooleanField("Активно", default=True)

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
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
        SUBMITTED = "submitted", "Сдано"
        GRADED = "graded", "Оценено"
        RETURNED = "returned", "Возвращено"

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Задание",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Студент",
        limit_choices_to={"role": "student"},
    )
    file = models.FileField(
        "Файл",
        upload_to="submissions/%Y/%m/%d/",
        help_text="Загрузите файл задания",
    )
    comment = models.TextField(
        "Комментарий",
        blank=True,
        help_text="Необязательный комментарий к заданию",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    grade = models.DecimalField(
        "Оценка",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    teacher_comment = models.TextField(
        "Комментарий преподавателя",
        blank=True,
        help_text="Обратная связь преподавателя по заданию",
    )
    submitted_at = models.DateTimeField("Сдано", auto_now_add=True)
    graded_at = models.DateTimeField("Оценено", null=True, blank=True)

    class Meta:
        verbose_name = "Сдача задания"
        verbose_name_plural = "Сдачи заданий"
        ordering = ["-submitted_at"]
        unique_together = ["assignment", "student"]

    def __str__(self) -> str:
        return f"{self.student.username} - {self.assignment.title}"

    def get_absolute_url(self) -> str:
        return reverse("assignments:submission_detail", kwargs={"pk": self.pk})
