from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import AdminUserCreationForm, LoginForm

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


@login_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    user: User = request.user  # type: ignore[assignment]
    if not user.is_admin():
        messages.error(request, "You do not have access to the admin dashboard.")
        return _redirect_for_role(user)

    if request.method == "POST":
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("admin_dashboard")
    else:
        form = AdminUserCreationForm()

    users = User.objects.exclude(pk=request.user.pk).order_by("role", "username")

    context: Dict[str, Any] = {
        "form": form,
        "users": users,
    }
    return render(request, "core/admin_dashboard.html", context)


@login_required
def teacher_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "core/teacher_dashboard.html")


@login_required
def student_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "core/student_dashboard.html")

