from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Classroom(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="teaching_classrooms",
        blank=True,
        limit_choices_to={"role": "TEACHER"},
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT,
    )

    student_class = models.ForeignKey(
        "Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )

    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN or self.is_superuser

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Roles.ADMIN
        if self.role != self.Roles.STUDENT:
            self.student_class = None
        super().save(*args, **kwargs)


class Course(models.Model):
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="courses",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class LearningMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to="materials/%Y/%m/", blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_materials",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.title


class Task(models.Model):
    class TaskType(models.TextChoices):
        PROJECT = "PROJECT", "Project"
        RESEARCH = "RESEARCH", "Research"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.PROJECT)
    rules = models.TextField(blank=True, help_text="Instructions and rules for the task")
    is_group_task = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class TaskGroup(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=100)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="task_groups",
        blank=True,
        limit_choices_to={"role": "STUDENT"},
    )

    class Meta:
        unique_together = [["task", "name"]]

    def __str__(self) -> str:
        return f"{self.task.title} – {self.name}"


class TaskSubmission(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="submissions")
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    group = models.ForeignKey(
        TaskGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="submissions",
    )
    content = models.TextField(blank=True)
    file = models.FileField(upload_to="submissions/%Y/%m/", blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_submissions",
    )

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"{self.task.title} by {self.submitted_by.username}"
