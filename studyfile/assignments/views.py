from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import QuerySet
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

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
        if user.is_teacher or user.is_admin:
            # Teachers see their own assignments
            return Assignment.objects.filter(teacher=user).select_related(
                "subject",
                "subject__study_group",
            )
        # Students see assignments for their group (via subject)
        if user.study_group:
            return Assignment.objects.filter(
                subject__study_group=user.study_group,
                is_active=True,
            ).select_related("subject", "teacher", "subject__study_group")
        return Assignment.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

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
        messages.success(self.request, _("Assignment created successfully."))
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
        messages.success(self.request, _("Assignment updated successfully."))
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
        messages.success(request, _("Assignment deleted successfully."))
        return super().delete(request, *args, **kwargs)


# ==================== Submission Views ====================


class SubmissionCreateView(LoginRequiredMixin, CreateView):
    """Create view for submissions - students only."""

    model = Submission
    form_class = SubmissionForm
    template_name = "assignments/submission_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_student:
            return HttpResponseForbidden(_("Only students can submit assignments."))
        self.assignment = get_object_or_404(Assignment, pk=kwargs["assignment_pk"])

        # Check if student is in target group (via subject)
        if request.user.study_group != self.assignment.subject.study_group:
            return HttpResponseForbidden(_("You are not assigned to this assignment."))

        # Check if already submitted
        if Submission.objects.filter(
            assignment=self.assignment,
            student=request.user,
        ).exists():
            messages.warning(request, _("You have already submitted this assignment."))
            return redirect("assignments:detail", pk=self.assignment.pk)

        # Check due date
        if self.assignment.due_date and self.assignment.due_date < timezone.now():
            messages.error(request, _("The deadline for this assignment has passed."))
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
        messages.success(self.request, _("Assignment submitted successfully."))
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

    def form_valid(self, form):
        form.instance.graded_at = timezone.now()
        messages.success(self.request, _("Submission graded successfully."))
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
