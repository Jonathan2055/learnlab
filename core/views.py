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
    ClassroomForm,
    CourseForm,
    LearningMaterialForm,
    LoginForm,
    SubmissionFeedbackForm,
    TaskSubmissionForm,
    TaskForm,
    TaskGroupForm,
)
from .models import Classroom, Course, LearningMaterial, Task, TaskGroup, TaskSubmission

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
        identifier = form.cleaned_data["identifier"]
        password = form.cleaned_data["password"]

        user_obj = None
        # Accept either email or username.
        # If it looks like an email, try email first; otherwise try username.
        if "@" in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(username__iexact=identifier).first()

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
    tab = request.GET.get("tab", "users")
    q = (request.GET.get("q") or "").strip()

    create_user_form = None
    if tab == "users":
        if request.method == "POST":
            create_user_form = AdminUserCreationForm(request.POST)
            if create_user_form.is_valid():
                create_user_form.save()
                messages.success(request, "User created successfully.")
                return redirect(reverse("admin_dashboard") + "?tab=users")
        else:
            create_user_form = AdminUserCreationForm()

    users_qs: QuerySet = User.objects.exclude(pk=request.user.pk).order_by("role", "username")
    if q and tab == "users":
        users_qs = users_qs.filter(username__icontains=q) | users_qs.filter(email__icontains=q)

    classrooms_qs: QuerySet = Classroom.objects.all()
    if q and tab == "classes":
        classrooms_qs = classrooms_qs.filter(name__icontains=q)

    courses_qs: QuerySet = Course.objects.select_related("classroom").all()
    if q and tab == "courses":
        courses_qs = courses_qs.filter(name__icontains=q) | courses_qs.filter(classroom__name__icontains=q)

    context: Dict[str, Any] = {
        "tab": tab,
        "q": q,
        "form": create_user_form,
        "users": users_qs,
        "classrooms": classrooms_qs,
        "courses": courses_qs,
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
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom = form.save()
            messages.success(request, f"Class «{classroom.name}» created.")
            return redirect("admin_class_detail", classroom_id=classroom.pk)
    else:
        form = ClassroomForm()
    return render(request, "core/admin_class_form.html", {"form": form, "classroom": None})


@login_required
@_require_admin
def admin_class_detail(request: HttpRequest, classroom_id: int) -> HttpResponse:
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    teachers = classroom.teachers.all()
    students = classroom.students.all()
    courses = classroom.courses.all()
    unassigned_students = User.objects.filter(role=User.Roles.STUDENT, student_class__isnull=True)

    context: Dict[str, Any] = {
        "classroom": classroom,
        "teachers": teachers,
        "students": students,
        "courses": courses,
        "unassigned_students": unassigned_students,
    }
    return render(request, "core/admin_class_detail.html", context)

#assigning student to class
@login_required
@_require_admin
@require_http_methods(["POST"])
def admin_class_add_student(request: HttpRequest, classroom_id: int) -> HttpResponse:
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    student_id = request.POST.get("student_id")
    student = get_object_or_404(User, pk=student_id, role=User.Roles.STUDENT)

    if student.student_class is not None:
        messages.error(request, f"{student.username} is already assigned to another class.")
    else:
        student.student_class = classroom
        student.save()
        messages.success(request, f"{student.username} added to {classroom.name}.")

    return redirect("admin_class_detail", classroom_id=classroom_id)


@login_required
@_require_admin
@require_http_methods(["POST"])
def admin_class_remove_student(request: HttpRequest, classroom_id: int, student_id: int) -> HttpResponse:
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    student = get_object_or_404(User, pk=student_id, role=User.Roles.STUDENT, student_class=classroom)
    student.student_class = None
    student.save()
    messages.success(request, f"{student.username} removed from {classroom.name}.")
    return redirect("admin_class_detail", classroom_id=classroom_id)

@login_required
@_require_admin
@require_http_methods(["GET", "POST"])
def admin_class_edit(request: HttpRequest, course_id: int) -> HttpResponse:
    classroom = get_object_or_404(Classroom, pk=course_id)
    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            messages.success(request, "Class updated.")
            return redirect("admin_class_detail", classroom_id=classroom.pk)
    else:
        form = ClassroomForm(instance=classroom)
    return render(request, "core/admin_class_form.html", {"form": form, "classroom": classroom})


@login_required
@_require_admin
@require_http_methods(["POST"])
def admin_class_delete(request: HttpRequest, course_id: int) -> HttpResponse:
    classroom = get_object_or_404(Classroom, pk=course_id)
    name = classroom.name
    classroom.delete()
    messages.success(request, f"Class «{name}» deleted.")
    return redirect("admin_dashboard")


@login_required
@_require_admin
@require_http_methods(["GET", "POST"])
def admin_course_create(request: HttpRequest, classroom_id: int) -> HttpResponse:
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course «{course.name}» created.")
            return redirect("admin_class_detail", classroom_id=course.classroom_id)
    else:
        form = CourseForm(initial={"classroom": classroom})
    return render(request, "core/admin_course_form.html", {"form": form, "classroom": classroom, "course": None})


@login_required
@_require_admin
@require_http_methods(["GET", "POST"])
def admin_course_edit(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated.")
            return redirect("admin_class_detail", classroom_id=course.classroom_id)
    else:
        form = CourseForm(instance=course)
    return render(
        request,
        "core/admin_course_form.html",
        {"form": form, "classroom": course.classroom, "course": course},
    )


@login_required
@_require_admin
@require_http_methods(["POST"])
def admin_course_delete(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    classroom_id = course.classroom_id
    name = course.name
    course.delete()
    messages.success(request, f"Course «{name}» deleted.")
    return redirect("admin_class_detail", classroom_id=classroom_id)


# ---- Teacher Dashboard ----
@login_required
@_require_teacher
def teacher_dashboard(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    classrooms = Classroom.objects.filter(teachers=request.user)
    if q:
        classrooms = classrooms.filter(name__icontains=q)
    return render(request, "core/teacher_dashboard.html", {"classrooms": classrooms, "q": q})


@login_required
@_require_teacher
def teacher_class_detail(request: HttpRequest, classroom_id: int) -> HttpResponse:
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    if request.user not in classroom.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    courses = classroom.courses.all()
    context: Dict[str, Any] = {
        "classroom": classroom,
        "courses": courses,
    }
    return render(request, "core/teacher_class_detail.html", context)


@login_required
@_require_teacher
def teacher_course_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.user not in course.classroom.teachers.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_dashboard")

    q = (request.GET.get("q") or "").strip()
    materials = course.materials.all()
    tasks = course.tasks.all()
    if q:
        materials = materials.filter(title__icontains=q)
        tasks = tasks.filter(title__icontains=q)

    context: Dict[str, Any] = {
        "course": course,
        "classroom": course.classroom,
        "materials": materials,
        "tasks": tasks,
        "q": q,
    }
    return render(request, "core/teacher_course_detail.html", context)


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_material_upload(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.user not in course.classroom.teachers.all():
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
            return redirect("teacher_course_detail", course_id=course.pk)
    else:
        form = LearningMaterialForm()
    return render(request, "core/teacher_material_form.html", {"form": form, "course": course})


@login_required
@_require_teacher
@require_http_methods(["POST"])
def teacher_material_delete(request: HttpRequest, material_id: int) -> HttpResponse:
    material = get_object_or_404(LearningMaterial, pk=material_id)
    course_id = material.course_id
    if request.user not in material.course.classroom.teachers.all():
        messages.error(request, "You are not allowed to delete this material.")
        return redirect("teacher_dashboard")
    material.delete()
    messages.success(request, "Material deleted.")
    return redirect("teacher_course_detail", course_id=course_id)


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_task_create(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.user not in course.classroom.teachers.all():
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
    if request.user not in task.course.classroom.teachers.all():
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
    if request.user not in task.course.classroom.teachers.all():
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
    if request.user not in task.course.classroom.teachers.all():
        messages.error(request, "You are not allowed to delete this task.")
        return redirect("teacher_dashboard")
    task.delete()
    messages.success(request, "Task deleted.")
    return redirect("teacher_course_detail", course_id=course_id)


@login_required
@_require_teacher
@require_http_methods(["GET", "POST"])
def teacher_task_group_create(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=task_id)
    if request.user not in task.course.classroom.teachers.all():
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
    if request.user not in submission.task.course.classroom.teachers.all():
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
    user: User = request.user  # type: ignore[assignment]
    if user.role != User.Roles.STUDENT:
        return _redirect_for_role(user)

    classroom = user.student_class
    courses = Course.objects.filter(classroom=classroom) if classroom else Course.objects.none()
    q = (request.GET.get("q") or "").strip()
    if q and classroom:
        courses = courses.filter(name__icontains=q)

    upcoming_deadlines = []
    if classroom:
        from django.utils import timezone

        now = timezone.now()
        # Completed tasks for the student (individual submissions or any group submissions for groups they belong to)
        group_ids = list(TaskGroup.objects.filter(students=user).values_list("id", flat=True))
        completed_task_ids = set(
            list(TaskSubmission.objects.filter(submitted_by=user).values_list("task_id", flat=True))
            + list(TaskSubmission.objects.filter(group_id__in=group_ids).values_list("task_id", flat=True))
        )
        upcoming_deadlines = (
            Task.objects.filter(course__classroom=classroom, due_date__isnull=False, due_date__gte=now)
            .exclude(pk__in=completed_task_ids)
            .select_related("course", "course__classroom")
            .order_by("due_date")[:8]
        )
    return render(
        request,
        "core/student_dashboard.html",
        {"classroom": classroom, "courses": courses, "q": q, "upcoming_deadlines": upcoming_deadlines},
    )


@login_required
def student_course_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    user: User = request.user  # type: ignore[assignment]
    if user.role != User.Roles.STUDENT:
        return _redirect_for_role(user)
    course = get_object_or_404(Course, pk=course_id)
    if not user.student_class or course.classroom_id != user.student_class_id:
        messages.error(request, "You do not have access to this course.")
        return redirect("student_dashboard")

    tab = request.GET.get("tab", "tasks")
    q = (request.GET.get("q") or "").strip()
    materials = course.materials.all()
    tasks = course.tasks.all()
    if q:
        materials = materials.filter(title__icontains=q)
        tasks = tasks.filter(title__icontains=q)

    submissions = TaskSubmission.objects.filter(task__course=course, submitted_by=user)
    grades_by_task = {s.task_id: s for s in submissions}

    return render(
        request,
        "core/student_course_detail.html",
        {
            "course": course,
            "classroom": course.classroom,
            "tab": tab,
            "q": q,
            "materials": materials,
            "tasks": tasks,
            "grades_by_task": grades_by_task,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def student_task_detail(request: HttpRequest, task_id: int) -> HttpResponse:
    user: User = request.user  # type: ignore[assignment]
    if user.role != User.Roles.STUDENT:
        return _redirect_for_role(user)
    task = get_object_or_404(Task, pk=task_id)
    if not user.student_class or task.course.classroom_id != user.student_class_id:
        messages.error(request, "You do not have access to this task.")
        return redirect("student_dashboard")

    group = None
    if task.is_group_task:
        group = TaskGroup.objects.filter(task=task, students=user).first()
        if not group:
            messages.error(request, "This is a group task and you are not assigned to a group yet.")
            return redirect("student_course_detail", course_id=task.course_id)

    existing = None
    if task.is_group_task and group:
        existing = TaskSubmission.objects.filter(task=task, group=group).first()
    else:
        existing = TaskSubmission.objects.filter(task=task, submitted_by=user).first()

    if request.method == "POST":
        if existing:
            messages.error(request, "A submission already exists for this task.")
            return redirect("student_task_detail", task_id=task.pk)
        form = TaskSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.task = task
            submission.submitted_by = user
            submission.group = group
            submission.save()
            messages.success(request, "Submission uploaded.")
            return redirect("student_course_detail", course_id=task.course_id)
    else:
        form = TaskSubmissionForm()

    return render(
        request,
        "core/student_task_detail.html",
        {"task": task, "course": task.course, "classroom": task.course.classroom, "form": form, "existing": existing, "group": group},
    )


@login_required
def student_portfolio(request: HttpRequest) -> HttpResponse:
    user: User = request.user  # type: ignore[assignment]
    if user.role != User.Roles.STUDENT:
        return _redirect_for_role(user)

    submissions = (
        TaskSubmission.objects.select_related("task", "task__course", "task__course__classroom")
        .filter(submitted_by=user)
        .order_by("-submitted_at")
    )
    return render(request, "core/student_portfolio.html", {"submissions": submissions})


@login_required
def student_portfolio_pdf(request: HttpRequest) -> HttpResponse:
    user: User = request.user  # type: ignore[assignment]
    if user.role != User.Roles.STUDENT:
        return _redirect_for_role(user)

    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    submissions = (
        TaskSubmission.objects.select_related("task", "task__course", "task__course__classroom")
        .filter(submitted_by=user)
        .order_by("task__course__name", "task__title")
    )

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, "LearnLab – Student Portfolio")
    y -= 22
    c.setFont("Helvetica", 12)
    c.drawString(72, y, f"Student: {user.get_full_name() or user.username}")
    y -= 28

    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Completed work (submitted tasks/projects)")
    y -= 18
    c.setFont("Helvetica", 10)

    for s in submissions:
        grade_text = ""
        if s.task.is_graded and s.grade is not None:
            if s.task.grading_mode == "PERCENTAGE":
                grade_text = f" · grade {s.grade} / 100%"
            else:
                grade_text = f" · grade {s.grade} / {s.task.max_score}"

        link_text = f" · link: {s.link}" if s.link else ""

        base_line = (
            f"- {s.task.title} ({s.task.get_task_type_display()}) · "
            f"{s.task.course.name} · submitted {s.submitted_at.strftime('%Y-%m-%d')}{grade_text}{link_text}"
        )

        if y < 72:
            c.showPage()
            y = height - 72
            c.setFont("Helvetica", 10)
        c.drawString(72, y, base_line[:120])
        y -= 14

        if s.skills_gained:
            skills = [x.strip() for x in s.skills_gained.splitlines() if x.strip()]
            if skills:
                if y < 72:
                    c.showPage()
                    y = height - 72
                    c.setFont("Helvetica", 10)
                c.drawString(80, y, "Skills:")
                y -= 12
                c.setFont("Helvetica", 9)
                for skill in skills[:8]:
                    if y < 72:
                        c.showPage()
                        y = height - 72
                        c.setFont("Helvetica", 9)
                    c.drawString(92, y, f"- {skill}"[:95])
                    y -= 11
                c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
    buffer.seek(0)

    from django.http import FileResponse

    filename = f"learnlab_portfolio_{user.username}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)
