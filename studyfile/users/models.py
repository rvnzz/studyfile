from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.urls import reverse


class StudyGroup(models.Model):
    """Study group for students."""

    name = models.CharField("Название группы", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    """Subject/course in the curriculum - each subject belongs to one study group."""

    name = models.CharField("Название предмета", max_length=200)
    code = models.CharField("Код предмета", max_length=20, blank=True)
    description = models.TextField("Описание", blank=True)
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name="Группа",
        null=True,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ["study_group", "name"]
        unique_together = ["name", "study_group"]

    def __str__(self) -> str:
        name_str = f"{self.code} - {self.name}" if self.code else self.name
        if self.study_group:
            return f"{name_str} ({self.study_group.name})"
        return name_str


class UserRole(models.TextChoices):
    """User role choices."""

    ADMIN = "admin", "Администратор"
    TEACHER = "teacher", "Преподаватель"
    STUDENT = "student", "Студент"


class User(AbstractUser):
    """
    Default custom user model for StudyFile.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField("Имя пользователя", blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    role = models.CharField(
        "Роль",
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
    )
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="Группа",
    )
    is_approved = models.BooleanField(
        "Одобрен",
        default=False,
        help_text="Указывает, была ли учетная запись одобрена администратором.",
    )

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def is_teacher(self) -> bool:
        return self.role == UserRole.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT


class TeacherSubject(models.Model):
    """Assignment of teachers to subjects."""

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="teaching_subjects",
        verbose_name="Преподаватель",
        limit_choices_to={"role": UserRole.TEACHER},
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="teachers",
        verbose_name="Предмет",
    )
    assigned_at = models.DateTimeField("Назначено", auto_now_add=True)

    class Meta:
        verbose_name = "Назначение преподавателя"
        verbose_name_plural = "Назначения преподавателей"
        unique_together = ["teacher", "subject"]
        ordering = ["teacher", "subject"]

    def __str__(self) -> str:
        return f"{self.teacher.username} - {self.subject.name}"
