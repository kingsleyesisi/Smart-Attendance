from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)

class CustomUserManager(BaseUserManager):
    def create_user(self, matric_number, email, password=None, **extra_fields):
        if not matric_number:
            raise ValueError("The Matric Number must be set")
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(matric_number=matric_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matric_number, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(matric_number, email, password, **extra_fields)

class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('coordinator', 'Coordinator'),
        ('student', 'Student'),
    )
    
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    matric_number = models.CharField(max_length=50, unique=True, blank=True, null=True)  # Ensure uniqueness
    
    username = None 
    USERNAME_FIELD = 'matric_number'  # Use matric_number for authentication
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()  # Attach the custom manager

    def __str__(self):
        return f"{self.matric_number} ({self.role})"