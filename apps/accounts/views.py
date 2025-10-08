from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer, LoginSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsCoordinator
from rest_framework.permissions import IsAdminUser
from backend.tasks import send_class_reminders
from apps.accounts.models import ClassSession, CustomUser
from backend.tasks import send_class_reminders
from django.utils.timezone import now, timedelta
from .models import Course, RegisterCourse
from .serializers import CourseSerializer


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    # register and save user
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # JWT tokens generation
        refresh = RefreshToken.for_user(user)
        token_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        headers = self.get_success_headers(serializer.data)
        return Response(
            {**serializer.data, **token_data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


# login viewpoint
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)


# logout viewpoint
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."})
        except Exception:
            return Response({"detail": "Invalid token."}, status=400)


# test class
class ProfileDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "first_name": user.first_name,
                "middle_name": user.middle_name,
                "last_name": user.last_name,
                "email": user.email,
                "mat_no": user.mat_no,
                "level": user.level,
                "department": user.department,
            }
        )


# Coordinator
class CoordinatorDashboard(APIView):
    permission_classes = [IsAuthenticated, IsCoordinator]

    def get(self, request):
        return Response({"message": "You are a  Coordinator"})


class TriggerReminderView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        # Create a test session starting 5 minutes from now
        session = ClassSession.objects.create(
            title="API Trigger Test Class", start_time=now() + timedelta(minutes=5)
        )

        # Add all students in DB to the session
        students = CustomUser.objects.filter(role="student")
        if not students.exists():
            return Response(
                {"message": "No students found in the database."}, status=400
            )

        session.students.add(*students)
        # Trigger the reminder task synchronously (for testing)
        send_class_reminders()  # runs immediately

        # trigger async for live with celery use
        send_class_reminders.delay()
        return Response(
            {
                "message": f"Test session created and reminder sent to {students.count()} students."
            }
        )


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]


# Student enrolls in a course
class RegisterAllCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = request.user
        level = student.level

        # Fetch all courses for that level
        courses = Course.objects.filter(level=level)

        enrolled = []
        already = []

        for course in courses:
            obj, created = RegisterCourse.objects.get_or_create(
                student=student, course=course
            )
            if created:
                enrolled.append(
                    {"code": course.code, "title": course.title, "level": course.level}
                )
            else:
                already.append(course.code)

        return Response(
            {
                "message": f"Processed courses for {level} level student",
                "newly_enrolled": enrolled,
                "already_enrolled": already,
            },
            status=status.HTTP_201_CREATED,
        )


# List student’s enrolled courses
class MyCoursesView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(register_courses__student=self.request.user)


# when testing with celery create a class session in django shell
# use this to reset all class session
# from apps.accounts.models import ClassSession
# ClassSession.objects.filter(reminder_sent=True).update(reminder_sent=False)
