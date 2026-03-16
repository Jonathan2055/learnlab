from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import (
    AdminUserCreationForm,
    AdminUserEditForm,
    CourseForm,
    LearningMaterialForm,
    LoginForm,
    SubmissionFeedbackForm,
    TaskForm,
    TaskGroupForm,
)
from .models import Course, LearningMaterial, Task, TaskGroup, TaskSubmission

User = get_user_model()


def _redirect_for_role(user: User) -> HttpResponse:
    if user.is_admin():
        return redirect("admin_dashboard")
    if user.role == User.Roles.TEACHER:
        return redirect("teacher_dashboard")
    return redirect("student_dashboard")


def login_view(request: HttpRequest, admin_login: bool = False) -> HttpResponse:
    if request.user.is_authenticated:
        return _redirect_for_role(request.user)  # type: ignore[arg-type]

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user_obj = None

        user = None
        if user_obj:
            user = authenticate(
                request,
                username=user_obj.username,
                password=password,
            )

        if user is None:
            messages.error(request, "Invalid credentials. Please try again.")
        else:
            if admin_login and not user.is_admin():
                messages.error(
                    request,
                    "You do not have administrator access.",
                )
            else:
                login(request, user)
                return _redirect_for_role(user)

    context: Dict[str, Any] = {
        "form": form,
        "is_admin_login": admin_login,
    }
    return render(request, "core/login.html", context)


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return _redirect_for_role(request.user)  # type: ignore[arg-type]


def _require_admin(view):
    def wrapped(request: HttpRequest, *args, **kwargs):
        user: User = request.user  # type: ignore[assignment]
        if not user.is_authenticated or not user.is_admin():
            messages.error(request, "You do not have access to this page.")
            return redirect("login")
        return view(request, *args, **kwargs)
    return wrapped


def _require_teacher(view):
    def wrapped(request: HttpRequest, *args, **kwargs):
        user: User = request.user  # type: ignore[assignment]
        if not user.is_authenticated or user.role != User.Roles.TEACHER:
            messages.error(request, "You do not have access to this page.")
            return redirect("login")
        return view(request, *args, **kwargs)
    return wrapped


# ---- Admin Dashboard ----
@login_required
@_require_admin
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("admin_dashboard")
    else:
        form = AdminUserCreationForm()

    users: QuerySet = User.objects.exclude(pk=request.user.pk).order_by("role", "username")
    courses: QuerySet = Course.objects.all()

    context: Dict[str, Any] = {
        "form": form,
        "users": users,
        "courses": courses,
    }
    return render(request, "core/admin_dashboard.html", context)


@login_required
@_require_admin
@require_http_methods(["GET", "POST"])
def admin_user_edit(request: HttpRequest, user_id: int) -> HttpResponse:
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser:
        messages.error(request, "Cannot edit superuser.")
        return redirect("admin_dashboard")

    if request.method == "POST":
        form = AdminUserEditForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("admin_dashboard")
    else:
        form = AdminUserEditForm(instance=target)

    return render(request, "core/admin_user_edit.html", {"form": form, "target_user": target})


@login_required
@_require_admin
@require_http_methods(["POST"])
def admin_user_delete(request: HttpRequest, user_id: int) -> HttpResponse:
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser:
        messages.error(request, "Cannot delete superuser.")
    else:
        target.delete()
        messages.success(request, "User deleted.")
    return redirect("admin_dashboard")


@login_required
@_require_admin
@require_http_methods(["GET", "POST"])
def admin_class_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Class «{course.name}» created.")
            return redirect("admin_class_detail", course_id=course.pk)
    else:
        form = CourseForm()
    return render(request, "core/admin_class_form.html", {"form": form, "course": None})


@login_required
@_require_admin
def admin_class_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    teachers = course.teachers.all()
    students = course.students.all()
    context: Dict[str, Any] = {
        "course": course,
        "teachers": teachers,
        "students": students,
    }
    return render(request, "core/admin_class_detail.html", context)


@login_required
@_require_admin
@require_http_methods(["GET", "POST"])
def admin_class_edit(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Class updated.")
            return redirect("admin_class_detail", course_id=course.pk)
    else:
        form = CourseForm(instance=course)
    return render(request, "core/admin_class_form.html", {"form": form, "course": course})


@login_required
@_require_admin
@require_http_methods(["POST"])
def admin_class_delete(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    name = course.name
    course.delete()
    messages.success(request, f"Class «{name}» deleted.")
    return redirect("admin_dashboard")


# ---- Teacher Dashboard ----
@login_required
@_require_teacher
def teacher_dashboard(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.filter(teachers=request.user)
    return render(request, "core/teacher_dashboard.html", {"courses": courses})


@login_required
@_require_teacher
def teacher_class_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.user not in course.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    materials = course.materials.all()
    tasks = course.tasks.all()
    context: Dict[str, Any] = {
        "course": course,
        "materials": materials,
        "tasks": tasks,
    }
    return render(request, "core/teacher_class_detail.html", context)


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_material_upload(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.user not in course.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    if request.method == "POST":
        form = LearningMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.uploaded_by = request.user
            material.save()
            messages.success(request, "Material uploaded.")
            return redirect("teacher_class_detail", course_id=course.pk)
    else:
        form = LearningMaterialForm()
    return render(request, "core/teacher_material_form.html", {"form": form, "course": course})


@login_required
@_require_teacher
@require_http_methods(["POST"])
def teacher_material_delete(request: HttpRequest, material_id: int) -> HttpResponse:
    material = get_object_or_404(LearningMaterial, pk=material_id)
    course_id = material.course_id
    if request.user not in material.course.teachers.all():
        messages.error(request, "You are not allowed to delete this material.")
        return redirect("teacher_dashboard")
    material.delete()
    messages.success(request, "Material deleted.")
    return redirect("teacher_class_detail", course_id=course_id)


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_task_create(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.user not in course.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.course = course
            task.created_by = request.user
            task.save()
            messages.success(request, "Task created.")
            return redirect("teacher_task_detail", task_id=task.pk)
    else:
        form = TaskForm()
    return render(request, "core/teacher_task_form.html", {"form": form, "course": course, "task": None})


@login_required
@_require_teacher
def teacher_task_detail(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=task_id)
    if request.user not in task.course.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    groups = task.groups.all()
    submissions = task.submissions.all()
    context: Dict[str, Any] = {
        "task": task,
        "course": task.course,
        "groups": groups,
        "submissions": submissions,
    }
    return render(request, "core/teacher_task_detail.html", context)


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_task_edit(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=task_id)
    if request.user not in task.course.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect("teacher_task_detail", task_id=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, "core/teacher_task_form.html", {"form": form, "course": task.course, "task": task})


@login_required
@_require_teacher
@require_http_methods(["POST"])
def teacher_task_delete(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=task_id)
    course_id = task.course_id
    if request.user not in task.course.teachers.all():
        messages.error(request, "You are not allowed to delete this task.")
        return redirect("teacher_dashboard")
    task.delete()
    messages.success(request, "Task deleted.")
    return redirect("teacher_class_detail", course_id=course_id)


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_task_group_create(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=task_id)
    if request.user not in task.course.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    if not task.is_group_task:
        messages.error(request, "This task is not a group task.")
        return redirect("teacher_task_detail", task_id=task.pk)

    if request.method == "POST":
        form = TaskGroupForm(request.POST, course=task.course)
        if form.is_valid():
            group = form.save(commit=False)
            group.task = task
            group.save()
            form.save_m2m()
            messages.success(request, f"Group «{group.name}» created.")
            return redirect("teacher_task_detail", task_id=task.pk)
    else:
        form = TaskGroupForm(course=task.course)
    return render(request, "core/teacher_group_form.html", {"form": form, "task": task})


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_submission_grade(request: HttpRequest, submission_id: int) -> HttpResponse:
    from django.utils import timezone

    submission = get_object_or_404(TaskSubmission, pk=submission_id)
    if request.user not in submission.task.course.teachers.all():
        messages.error(request, "You are not assigned to grade this submission.")
        return redirect("teacher_dashboard")

    if request.method == "POST":
        form = SubmissionFeedbackForm(request.POST, instance=submission)
        if form.is_valid():
            obj = form.save(commit=False)
            if not submission.task.is_graded:
                obj.grade = None
            obj.graded_by = request.user
            obj.graded_at = timezone.now()
            obj.save()
            messages.success(request, "Feedback saved.")
            return redirect("teacher_task_detail", task_id=submission.task_id)
    else:
        form = SubmissionFeedbackForm(instance=submission)
    return render(request, "core/teacher_submission_grade.html", {"form": form, "submission": submission})


# ---- Student Dashboard ----
@login_required
def student_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "core/student_dashboard.html")
