from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):
    """
    Custom user manager for User model with email and matric_number as authentication fields.
    """

    def create_user(self, email, matric_number, password=None, **extra_field):
        """Create and save a regular user with the given email, matric_number and password."""
        if not email:
            raise ValueError('The Email field must be set')
        if not matric_number:
            raise ValueError('The Matric Number field must be set')

        email = self.normalize_email(email)
        # Generate username from matric_number
        username = matric_number.lower().replace(" ", "_")
        user = self.model(
            email=email, 
            matric_number=matric_number,
            **extra_field)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, matric_number, password=None, **extra_field):
        """Create and save a superuser with the given email, matric_number and password."""
        extra_field.setdefault('is_staff', True)
        extra_field.setdefault('is_active', True)
        extra_field.setdefault('role', 'admin')
        extra_field.setdefault('is_verified', True)

        if extra_field.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
       
        return self.create_user(email, matric_number, password, **extra_field)
    
    def get_by_natural_key(self, username):
        """Allow authentication with either email or matric_number."""
        return self.get(
            models.Q(email=username) | models.Q(matric_number=username)
        )
    

class CoordinatorProfileManager(models.Manager):
    """Custom manager for CoordinatorProfile model."""
    
    def get_approved(self):
        """Return all approved coordinator profiles."""
        return self.filter(is_approved=True)
    
    def get_pending(self):
        """Return all pending coordinator profiles."""
        return self.filter(is_approved=False)
    
    def get_by_faculty(self, faculty):
        """Return coordinator profiles by faculty."""
        return self.filter(faculty=faculty)
    
    def get_by_department(self, department):
        """Return coordinator profiles by department."""
        return self.filter(department=department)
    
class StudentProfileManager(models.Manager):
    """Custom manager for StudentProfile model."""
    
    def get_by_faculty(self, faculty):
        """Return student profiles by faculty."""
        return self.filter(faculty=faculty)
    
    def get_by_department(self, department):
        """Return student profiles by department."""
        return self.filter(department=department)
    
    def get_by_year_level(self, year_level):
        """Return student profiles by level."""
        return self.filter(level=year_level)