from django.db import models
from django.contrib.auth.models import AbstractUser
# Student
class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(unique=True)
    matric_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=50)
    faculty = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)

    REQUIRED_FIELDS = ["first_name", "last_name", "email", "matric_number"],

    def __str__(self):
        return f"{self.username} ({self.matric_number})"
