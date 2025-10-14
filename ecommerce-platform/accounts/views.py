# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import EmailOtpRequestSerializer,EmailVerifySerializer,ResendOtpSerializer
from .models import EmailOtp

# Create your views here.
@api_view(['POST'])
def email_otp_request(request):
    serializer = EmailOtpRequestSerializer(data=request.data)
    if serializer.is_valid():
        user,otp = serializer.save()  # triggers create or update method of serializer
        try:
            
            user.save() # instance saved into db
            EmailOtp.objects.update_or_create(user=user,
                                            defaults={"otp": otp})
        except Exception as e:
            return Response({
                "error": "Unable to save otp , please try again later",
                "details": str(e),

            },status=status.HTTP_500_INTERNEL_SERVER_ERROR)

        return Response({
            "message": "OTP sent succesfuly. Please check your email",
            "user": {
                "id": user.id,
                "email": user.email,
                "first name": user.first_name,
                "last name": user.last_name,
                "is verified": user.is_verified
            }
        },status=status.HTTP_201_CREATED)
    

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def resend_otp(request):
    serializer = ResendOtpSerializer(data=request.data)
    if serializer.is_valid():
        user,otp = serializer.save()
        try:
            email_otp = EmailOtp.objects.update_or_create(user=user,
                                                          defaults={"otp": otp})
        except Exception as e:
            return Response({
                "message": "OTP resend is unsuccessfull.",
                "details": str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "OTP resent Successfully, Please check you email",
            "email": user.email
        },status=status.HTTP_201_CREATED)
    
    return Response({
        "message": "Invaild Data",
        "error": serializer.errors()
    },status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def email_verify(request):
    serializer = EmailVerifySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Email is verified successfully."
        },status=status.HTTP_201_CREATED)
     
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


