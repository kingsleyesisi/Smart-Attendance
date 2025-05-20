from rest_framework import serializers
from .models import User, Department
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    matric_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        login_field = attrs.get('matric_number') or attrs.get('email')  # Accept matric_number or email
        password = attrs.get('password')

        # Try to authenticate using matric_number first, then email
        user = User.objects.filter(matric_number=login_field).first() or User.objects.filter(email=login_field).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            if not user.is_approved:
                raise serializers.ValidationError("User account is not approved")
        else:
            raise serializers.ValidationError("Invalid matric number/email or password")

        data = super().validate(attrs)
        data['role'] = user.role
        data['is_approved'] = user.is_approved
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'role', 'matric_number', 'phone_number')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        if data['role'] == 'coordinator':
            if not data.get('phone_number'):
                raise serializers.ValidationError("Phone number is required for coordinators")
        elif data['role'] == 'student':
            if not data.get('matric_number'):
                raise serializers.ValidationError("Matric number is required for students")
            if not data.get('phone_number'):
                raise serializers.ValidationError("Phone number is required for students")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        
        # Handle coordinator and student-specific fields
        if validated_data['role'] == 'coordinator':
            validated_data['is_approved'] = False
        elif validated_data['role'] == 'student':
            validated_data['is_approved'] = True  # Students might not need approval
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user