from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import User
from .serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from .tasks import send_approval_request
from django.utils.translation import gettext_lazy as _

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send approval email if coordinator
        if user.role == 'coordinator':
            send_approval_request.delay(user.id)
        
        return Response({
            'message': 'User created successfully. Coordinator approval pending' if user.role == 'coordinator' else 'User created successfully',
            'user_id': user.id,
            'role': user.role,
            'phone_number': user.phone_number,
            'matric_number': user.matric_number
        }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def approve_coordinator(request, user_id):
    try:
        user = User.objects.get(id=user_id, role='coordinator')
        user.is_approved = True
        user.save()
        # send_approval_notification.delay(user.email)
        return Response({'status': 'approved'})
    except User.DoesNotExist:
        return Response({'error': 'Coordinator not found'}, status=404)
