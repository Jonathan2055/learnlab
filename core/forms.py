from django import forms
from django.contrib.auth import get_user_model

from .models import Classroom, Course, LearningMaterial, Task, TaskGroup, TaskSubmission

User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "name@school.edu"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "********"}),
    )


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Create a password"}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat the password"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "role"]

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        password = self.cleaned_data["password1"]
        user.set_password(password)
        if user.role == User.Roles.ADMIN:
            user.is_staff = True
        if commit:
            user.save()
        return user


class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "role", "student_class"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self.instance, "role", None) != User.Roles.STUDENT:
            self.fields["student_class"].disabled = True


class ClassroomForm(forms.ModelForm):
    teachers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role=User.Roles.TEACHER),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Classroom
        fields = ["name", "description", "teachers"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["classroom", "name", "description"]


class LearningMaterialForm(forms.ModelForm):
    class Meta:
        model = LearningMaterial
        fields = ["title", "content", "file"]


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "task_type", "rules", "is_group_task", "is_graded", "due_date"]
        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class TaskGroupForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = TaskGroup
        fields = ["name", "students"]

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            self.fields["students"].queryset = course.classroom.students.all()


class SubmissionFeedbackForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ["feedback", "grade"]


class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ["content", "file"]

