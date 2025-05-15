from django.shortcuts import render, response
from rest_framework.response import Response

# View to handle registration of new users (Student)
def index(request):
    
    return Response({"message": "Welcome to the student attendance platform"})