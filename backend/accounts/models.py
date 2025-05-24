from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re


from .manager import CustomUserManager, CoordinatorProfileManager, StudentProfileManager

class User(AbstractUser, PermissionsMixin):
    """
    Custom user model with email and matric_number as authentication fields.
    """

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('coordinator', 'Coordinator'),
        ('admin', 'Admin'),
    )

    # Validators 
    matric_number_validator = RegexValidator(
        regex=r'^[A-Z]{3}/\d{2}/\d{2}/\d{6}$',
        message='Matric number must be in the format ABC/12/34/123456 where ABC are Faculty, 12 and 34 are year of admission, and main mat number.',
        code='invalid_matric_number'
    )

    phone_number_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.',
        code='invalid_phone_number'
    )

    # Fields

    username = None  # Disable username field
    email = models.EmailField(unique=True, verbose_name='email address')
    matric_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[matric_number_validator],
        verbose_name='Matric Number'
        help_text='Format: ABC/12/34/123456 where ABC are Faculty, 12 and 34 are year of admission, and main mat number.'
    )
    phone_number = models.CharField(
        max_length=17,
        validators=[phone_number_validator],
        blank=True,
        null=True,
        verbose_name='Phone Number',
        help_text='Format: +1234567890. Up to 15 digits allowed.'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name='User Role'
    )
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')
    first_name = models.CharField(max_length=30, blank=True, verbose_name='First Name')
    last_name = models.CharField(max_length=30, blank=True, verbose_name='Last Name')
    is_active = models.BooleanField(default=True, verbose_name='Active Status')
    is_staff = models.BooleanField(default=False, verbose_name='Staff Status')
    is_verified = models.BooleanField(default=False, verbose_name='Email Verified')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Last Login')

    objects = CustomUserManager()


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['matric_number', 'first_name', 'last_name']

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def get_full_name(self):
        """Return the first_name plus last_name with a space inbetween."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name 
    
    def __str__(self):
        return f'{self.matric_number} - {self.get_full_name()}'
    
    def clean(self):
        """Validate user data before saving."""
        super().clean()

        # Normalize email
        if self.email:
            self.email = self.email.lower()

        # Normalize matric number
        if self.matric_number:
            self.matric_number = self.matric_number.upper()

    def save(self, *args, **kwargs):
        """Override save to perform additiaon validation."""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        """Check if the user is an admin."""
        return self.role == 'admin'
    
    @property
    def is_coordinator(self):
        """Check if the user is a coordinator."""
        return self.role == 'coordinator'
    
    @property
    def is_student(self):
        """Check if the user is a student."""
        return self.role == 'student'
    
    @property
    def is_approved_coordinator(self):
        """Check if the coordinator profile is approved."""
        if self.role != 'coordinator':
            return False
        try:
            return self.coordinator_profile.is_approved
        except CoordinatorProfile.DoesNotExist:
            return False
        
    @property
    def account_status(self):
        """Get detailed account status"""
        if self.role == 'admin':
            return {
                'status': 'active',
            }