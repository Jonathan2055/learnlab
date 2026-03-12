from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN or self.is_superuser
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Roles.ADMIN
        super().save(*args, **kwargs)


