# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import EmailOtpRequestSerializer,EmailVerifySerializer

# Create your views here.
@api_view(['POST'])
def email_otp_request(request):
    serializer = EmailOtpRequestSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()  # triggers create or update method of serializer
        return Response({
            "message": "OTP sent succesfuly. Please check your email"
        },status=status.HTTP_201_CREATED)
    

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def email_verify(request):
    serializer = EmailVerifySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Email is verified successfully."
        },status=status.HTTP_201_CREATED)
     
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
