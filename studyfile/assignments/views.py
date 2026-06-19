import io
import zipfile
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone

from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic import View

from studyfile.users.models import StudyGroup
from studyfile.users.models import User

from .forms import AssignmentForm
from .forms import SubmissionForm
from .forms import SubmissionGradeForm
from .models import Assignment
from .models import Submission


def is_teacher(user):
    return user.is_authenticated and (user.is_teacher or user.is_admin)


def is_admin(user):
    return user.is_authenticated and user.is_admin


class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_teacher(self.request.user)


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)


# ==================== Assignment Views ====================


class AssignmentListView(LoginRequiredMixin, ListView):
    """List view for assignments - different for teachers and students."""

    model = Assignment
    template_name = "assignments/assignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        queryset = Assignment.objects.all()

        if user.is_teacher or user.is_admin:
            # Teachers see their own assignments
            queryset = queryset.filter(teacher=user)
        elif user.is_student:
            # Students see assignments for their group (via subject)
            if user.study_group:
                queryset = queryset.filter(
                    subject__study_group=user.study_group,
                    is_active=True,
                )
            else:
                return Assignment.objects.none()

        # Apply group filter if provided
        group_filter = self.request.GET.get("group")
        if group_filter:
            queryset = queryset.filter(subject__study_group_id=group_filter)

        # Apply subject filter if provided
        subject_filter = self.request.GET.get("subject")
        if subject_filter:
            queryset = queryset.filter(subject_id=subject_filter)

        return queryset.select_related("subject", "teacher", "subject__study_group")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Add filter options for teachers/admins
        if user.is_teacher or user.is_admin:
            from studyfile.users.models import Subject

            context["study_groups"] = StudyGroup.objects.all()
            context["subjects"] = Subject.objects.all()
            context["selected_group"] = self.request.GET.get("group", "")
            context["selected_subject"] = self.request.GET.get("subject", "")

        if user.is_student and user.study_group:
            # Add submission status for each assignment
            assignments = context["assignments"]
            submission_map = {}
            for assignment in assignments:
                try:
                    submission = Submission.objects.get(
                        assignment=assignment,
                        student=user,
                    )
                    submission_map[assignment.id] = submission
                except Submission.DoesNotExist:
                    submission_map[assignment.id] = None
            context["submission_map"] = submission_map

        return context


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    """Detail view for an assignment."""

    model = Assignment
    template_name = "assignments/assignment_detail.html"
    context_object_name = "assignment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        user = self.request.user

        if user.is_teacher or user.is_admin:
            # Teachers see all submissions for this assignment
            context["submissions"] = Submission.objects.filter(
                assignment=assignment,
            ).select_related(
                "student",
            )
        elif user.is_student:
            # Students see their own submission if exists
            try:
                context["user_submission"] = Submission.objects.get(
                    assignment=assignment,
                    student=user,
                )
            except Submission.DoesNotExist:
                context["user_submission"] = None
            context["can_submit"] = (
                user.study_group == assignment.subject.study_group
                and assignment.is_active
                and (not assignment.due_date or assignment.due_date > timezone.now())
            )

        return context


class AssignmentCreateView(TeacherRequiredMixin, CreateView):
    """Create view for assignments - teachers only."""

    model = Assignment
    form_class = AssignmentForm
    template_name = "assignments/assignment_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Задание успешно создано.")
        return reverse("assignments:list")


class AssignmentUpdateView(TeacherRequiredMixin, UpdateView):
    """Update view for assignments - only the teacher who created it."""

    model = Assignment
    form_class = AssignmentForm
    template_name = "assignments/assignment_form.html"

    def get_queryset(self):
        # Teachers can only edit their own assignments
        if self.request.user.is_admin:
            return Assignment.objects.all()
        return Assignment.objects.filter(teacher=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Задание успешно обновлено.")
        return reverse("assignments:detail", kwargs={"pk": self.object.pk})


class AssignmentDeleteView(TeacherRequiredMixin, DeleteView):
    """Delete view for assignments - only the teacher who created it."""

    model = Assignment
    template_name = "assignments/assignment_confirm_delete.html"
    success_url = reverse_lazy("assignments:list")

    def get_queryset(self):
        if self.request.user.is_admin:
            return Assignment.objects.all()
        return Assignment.objects.filter(teacher=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Задание успешно удалено.")
        return super().delete(request, *args, **kwargs)


# ==================== Submission Views ====================


class SubmissionCreateView(LoginRequiredMixin, CreateView):
    """Create view for submissions - students only."""

    model = Submission
    form_class = SubmissionForm
    template_name = "assignments/submission_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_student:
            return HttpResponseForbidden("Только студенты могут сдавать задания.")
        self.assignment = get_object_or_404(Assignment, pk=kwargs["assignment_pk"])

        # Check if student is in target group (via subject)
        if request.user.study_group != self.assignment.subject.study_group:
            return HttpResponseForbidden("Вы не назначены на это задание.")

        # Check if already submitted
        if Submission.objects.filter(
            assignment=self.assignment,
            student=request.user,
        ).exists():
            messages.warning(request, "Вы уже сдали это задание.")
            return redirect("assignments:detail", pk=self.assignment.pk)

        # Check due date
        if self.assignment.due_date and self.assignment.due_date < timezone.now():
            messages.error(request, "Срок сдачи этого задания истек.")
            return redirect("assignments:detail", pk=self.assignment.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["assignment"] = self.assignment
        kwargs["student"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assignment"] = self.assignment
        return context

    def get_success_url(self):
        messages.success(self.request, "Задание успешно сдано.")
        return reverse("assignments:detail", kwargs={"pk": self.assignment.pk})


class SubmissionDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a submission."""

    model = Submission
    template_name = "assignments/submission_detail.html"
    context_object_name = "submission"

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher or user.is_admin:
            # Teachers see submissions for their assignments
            return Submission.objects.filter(assignment__teacher=user)
        # Students see only their own submissions
        return Submission.objects.filter(student=user)


class SubmissionGradeView(TeacherRequiredMixin, UpdateView):
    """View for grading submissions - teachers only."""

    model = Submission
    form_class = SubmissionGradeForm
    template_name = "assignments/submission_grade.html"

    def get_queryset(self):
        # Teachers can only grade submissions for their assignments
        if self.request.user.is_admin:
            return Submission.objects.all()
        return Submission.objects.filter(assignment__teacher=self.request.user)

    def get_initial(self):
        initial = super().get_initial()
        submission = self.get_object()
        if submission.ai_status == Submission.AIStatus.COMPLETED and submission.ai_grade is not None:
            if not submission.grade:
                initial["grade"] = submission.ai_grade
            if not submission.teacher_comment:
                initial["teacher_comment"] = submission.ai_feedback
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = self.get_object()
        context["has_ai_grade"] = (
            submission.ai_status == Submission.AIStatus.COMPLETED
            and submission.ai_grade is not None
        )
        return context

    def form_valid(self, form):
        form.instance.graded_at = timezone.now()
        messages.success(self.request, "Сдача успешно оценена.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("assignments:submission_detail", kwargs={"pk": self.object.pk})


# ==================== Teacher Views ====================


class TeacherSubmissionsListView(TeacherRequiredMixin, ListView):
    """List all submissions for assignments created by the teacher."""

    model = Submission
    template_name = "assignments/teacher_submissions.html"
    context_object_name = "submissions"

    def get_queryset(self):
        if self.request.user.is_admin:
            return Submission.objects.all().select_related("assignment", "student")
        return Submission.objects.filter(
            assignment__teacher=self.request.user,
        ).select_related("assignment", "student")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "")
        return context


class AssignmentSubmissionsDownloadView(TeacherRequiredMixin, View):
    """Download all submissions for an assignment as a ZIP archive."""

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)

        # Check permission - only teacher who created the assignment or admin can download
        if not request.user.is_admin and assignment.teacher != request.user:
            return HttpResponseForbidden(
                "У вас нет разрешения на скачивание этих сдач.",
            )

        submissions = Submission.objects.filter(assignment=assignment).select_related(
            "student",
        )

        if not submissions.exists():
            messages.warning(request, "Нет сдач для скачивания по этому заданию.")
            return redirect("assignments:detail", pk=pk)

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for submission in submissions:
                if submission.file:
                    file_path = submission.file.path
                    file_name = Path(file_path).name

                    # Create a unique filename with student info
                    student_display = submission.student.name or submission.student.username
                    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in student_display).strip()
                    original_ext = Path(file_name).suffix
                    new_filename = f"{safe_name}_{submission.pk}{original_ext}"

                    # Add file to ZIP
                    zip_file.write(file_path, new_filename)

        # Prepare response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type="application/zip")
        response["Content-Disposition"] = (
            f'attachment; filename="submissions_{assignment.title.replace(" ", "_")}.zip"'
        )

        return response


# ==================== Student Management Views ====================


class TeacherStudentsListView(TeacherRequiredMixin, ListView):
    """List students from groups related to teacher's assignments."""

    model = User
    template_name = "assignments/teacher_students.html"
    context_object_name = "students"

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        if user.is_admin:
            return User.objects.filter(role="student").select_related("study_group")

        from studyfile.users.models import StudyGroup

        teacher_groups = StudyGroup.objects.filter(
            subjects__assignments__teacher=user,
        ).distinct()

        return User.objects.filter(
            role="student",
            study_group__in=teacher_groups,
        ).select_related("study_group").distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group_filter"] = self.request.GET.get("group", "")
        from studyfile.users.models import StudyGroup

        if self.request.user.is_admin:
            context["study_groups"] = StudyGroup.objects.all()
        else:
            context["study_groups"] = StudyGroup.objects.filter(
                subjects__assignments__teacher=self.request.user,
            ).distinct()
        return context


class StudentSubmissionsView(TeacherRequiredMixin, ListView):
    """List all assignments for a student, showing submission status."""

    model = Assignment
    template_name = "assignments/student_submissions.html"
    context_object_name = "assignments"

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        self.student = get_object_or_404(User, pk=self.kwargs["student_pk"], role="student")

        queryset = Assignment.objects.filter(
            subject__study_group=self.student.study_group,
        )

        if not user.is_admin:
            queryset = queryset.filter(teacher=user)

        return queryset.select_related("subject", "subject__study_group")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student"] = self.student

        submissions = Submission.objects.filter(
            student=self.student,
            assignment__in=context["assignments"],
        ).select_related("assignment")
        context["submission_map"] = {s.assignment_id: s for s in submissions}

        return context


class StudentSubmissionsDownloadView(TeacherRequiredMixin, View):
    """Download all submissions of a student as a ZIP archive."""

    def get(self, request, student_pk):
        student = get_object_or_404(User, pk=student_pk, role="student")

        if request.user.is_admin:
            submissions = Submission.objects.filter(student=student).select_related(
                "assignment",
                "assignment__subject",
            )
        else:
            submissions = Submission.objects.filter(
                student=student,
                assignment__teacher=request.user,
            ).select_related("assignment", "assignment__subject")

        if not submissions.exists():
            messages.warning(request, "Нет работ для скачивания.")
            return redirect("assignments:teacher_students")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for submission in submissions:
                if submission.file:
                    file_path = submission.file.path
                    file_name = Path(file_path).name

                    assignment_title = "".join(
                        c if c.isalnum() or c in " _-" else "_"
                        for c in submission.assignment.title
                    ).strip()
                    original_ext = Path(file_name).suffix
                    new_filename = f"{assignment_title}_{submission.pk}{original_ext}"

                    zip_file.write(file_path, new_filename)

        zip_buffer.seek(0)
        student_display = student.name or student.username
        safe_name = "".join(
            c if c.isalnum() or c in " _-" else "_" for c in student_display
        ).strip()
        response = HttpResponse(zip_buffer.read(), content_type="application/zip")
        response["Content-Disposition"] = (
            f'attachment; filename="student_{safe_name}_submissions.zip"'
        )

        return response
