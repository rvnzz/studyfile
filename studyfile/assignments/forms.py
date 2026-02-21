from django import forms
from django.utils.translation import gettext_lazy as _

from studyfile.users.models import TeacherSubject

from .models import Assignment
from .models import Submission


class AssignmentForm(forms.ModelForm):
    """Form for creating and editing assignments."""

    class Meta:
        model = Assignment
        fields = [
            "title",
            "description",
            "subject",
            "due_date",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher
        if teacher:
            assigned_subjects = TeacherSubject.objects.filter(
                teacher=teacher,
            ).values_list(
                "subject_id",
                flat=True,
            )
            self.fields["subject"].queryset = self.fields["subject"].queryset.filter(
                id__in=assigned_subjects,
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.teacher:
            instance.teacher = self.teacher
        if commit:
            instance.save()
        return instance


class SubmissionForm(forms.ModelForm):
    """Form for submitting assignments."""

    class Meta:
        model = Submission
        fields = ["file", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={"rows": 3, "placeholder": _("Optional comment")},
            ),
        }

    def __init__(self, *args, assignment=None, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment
        self.student = student

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.assignment:
            instance.assignment = self.assignment
        if self.student:
            instance.student = self.student
        if commit:
            instance.save()
        return instance


class SubmissionGradeForm(forms.ModelForm):
    """Form for grading submissions."""

    class Meta:
        model = Submission
        fields = ["grade", "teacher_comment", "status"]
        widgets = {
            "teacher_comment": forms.Textarea(attrs={"rows": 4}),
        }
