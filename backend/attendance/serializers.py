from rest_framework import serializers
from .models import User, Department
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['is_approved'] = user.is_approved
        return token

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    department_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('email', 'password', 'role', 'department_code', 'matric_number')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['role'] == 'coordinator' and 'department_code' not in data:
            raise serializers.ValidationError("Department code required for coordinators")
        return data

    def create(self, validated_data):
        department_code = validated_data.pop('department_code', None)
        password = validated_data.pop('password')
        
        # Handle coordinator approval
        if validated_data['role'] == 'coordinator':
            validated_data['is_approved'] = False
            department = Department.objects.get(code=department_code)
            validated_data['department'] = department
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user