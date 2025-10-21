from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ClassSession, Course, CustomUser, RegisterCourse

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "first_name", "last_name", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser")
    ordering = ("email",)
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Role Information", {"fields": ("role",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )
    def delete_model(self, request, obj):
        # Cleanup related objects first
        Course.objects.filter(lecturer=obj).delete()
        RegisterCourse.objects.filter(student=obj).delete()
        for session in ClassSession.objects.filter(students=obj):
            session.students.remove(obj)

        # Finally delete the user
        super().delete_model(request, obj)
admin.site.register(Course)
