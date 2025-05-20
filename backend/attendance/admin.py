from django.contrib import admin
from .models import User, Department

admin.site.register(Department)
admin.site.register(User)