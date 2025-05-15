from django.db import models

class Student(models.Model):
    """
    Model for Students 
    """
    student_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mat_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.first_name + " " + self.last_name

