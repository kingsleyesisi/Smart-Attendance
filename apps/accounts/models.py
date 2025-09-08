from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=50)
    faculty = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    mat_no = models.CharField(max_length=20, unique=True)

    is_active = models.BooleanField(
        default=True
    )  # control student access (set to false and the student can't login)
    is_staff = models.BooleanField(
        default=False
    )  # staff access having the ability to log into /admin (lecturer access)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "mat_no"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email
