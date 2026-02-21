from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class StudyGroup(models.Model):
    """Study group for students."""

    name = models.CharField(_("Group Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Study Group")
        verbose_name_plural = _("Study Groups")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    """Subject/course in the curriculum - each subject belongs to one study group."""

    name = models.CharField(_("Subject Name"), max_length=200)
    code = models.CharField(_("Subject Code"), max_length=20, blank=True)
    description = models.TextField(_("Description"), blank=True)
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name=_("Study Group"),
        null=True,
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Subject")
        verbose_name_plural = _("Subjects")
        ordering = ["study_group", "name"]
        unique_together = ["name", "study_group"]

    def __str__(self) -> str:
        name_str = f"{self.code} - {self.name}" if self.code else self.name
        if self.study_group:
            return f"{name_str} ({self.study_group.name})"
        return name_str


class UserRole(models.TextChoices):
    """User role choices."""

    ADMIN = "admin", _("Administrator")
    TEACHER = "teacher", _("Teacher")
    STUDENT = "student", _("Student")


class User(AbstractUser):
    """
    Default custom user model for StudyFile.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    role = models.CharField(
        _("Role"),
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
        verbose_name=_("Study Group"),
    )
    is_approved = models.BooleanField(
        _("Is Approved"),
        default=False,
        help_text=_(
            "Designates whether the user account has been approved by an admin.",
        ),
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
        verbose_name=_("Teacher"),
        limit_choices_to={"role": UserRole.TEACHER},
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="teachers",
        verbose_name=_("Subject"),
    )
    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Teacher Subject")
        verbose_name_plural = _("Teacher Subjects")
        unique_together = ["teacher", "subject"]
        ordering = ["teacher", "subject"]

    def __str__(self) -> str:
        return f"{self.teacher.username} - {self.subject.name}"
