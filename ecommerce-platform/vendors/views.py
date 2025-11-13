# from django.shortcuts import render, redirect
# from django.http import JsonResponse
# from accounts.models import Customer
# from .serializers import CustomerSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from django.core.mail import send_mail
# from django.conf import settings
from django.contrib.auth import get_user_model
from .serializers import (VendorRegisterOTPSerializer,VendorVerifyOTPSerializer,
                          MobileOtpRequestSerializer,VerifyMobileOTPSerializer,
                          RegisterVendorSerializer)
from .models import Vendor,VendorEmailOtp,VendorMobileOtp
from ecommerce_platform.utils import generate_otp
User = get_user_model()

@api_view(['POST'])
@permission_classes([])
def vendor_register_otp(request):
    serializer = VendorRegisterOTPSerializer(data=request.data)
    if serializer.is_valid():
        otp = generate_otp()
        business_email = serializer.validated_data.get('business_email')
        try:
            send_mail(
                subject="Verify Email at ShopWaveX using OTP",                    
                message=f"your otp is {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[business_email],
                fail_silently=False
            )
        except Exception as e:
               return Response({
                    "message": "Unable to send message"
               },status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            # print("Jai Shree Ram")
            # print(otp)
            # print(business_email)
            VendorEmailOtp.objects.update_or_create(
                business_email=serializer.validated_data.get('business_email'),
                defaults={"otp": otp,
                          "isUsed": False,
                          "is_verified": False}
            )
        except Exception as e:
            return Response({
                "error": "Unable to process otp request.",
                "message": str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "message": "OTP sent successfully. Check your email."
        },status=status.HTTP_200_OK)
    
    return Response({
        "message": "Invaild Data",
        "error": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST'])
@permission_classes([])
def vendor_verify_otp(request):
     serializer = VendorVerifyOTPSerializer(data=request.data)

     if serializer.is_valid():
          emailotp = serializer.save()
          return Response({
               "message": "Email is verified successfully.",
               "business_email": emailotp.business_email
          },status=status.HTTP_201_CREATED)
     
     return Response({
          "message": "Invalid Data",
          "errors": serializer.errors,
     },status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def request_mobile_otp(request):
     serializer = MobileOtpRequestSerializer(data=request.data)
     if serializer.is_valid():
          mobile_no = serializer.validated_data.get('mobile_number')
          otp = generate_otp() #6 digit
          try:
               VendorMobileOtp.objects.update_or_create(
                    phone=mobile_no,
                    defaults={
                         "otp": otp,
                         "isUsed": False,
                         "is_verified": False
                    }
               )
          except Exception as e:
               return Response({
                    "message": "Unable to process mobile otp."
               },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
          
          return Response({
               "message": "Sorry,Unable to send otp on mobile number. contact admin."
          },status=status.HTTP_200_OK)
     
     return Response({
               "message": "Invalid Data",
               "error": serializer.errors
          },status=status.HTTP_400_BAD_REQUEST)
     
@api_view(['POST'])
@permission_classes([])
def verify_mobile_otp(request):
    serializer = VerifyMobileOTPSerializer(data=request.data)

    if serializer.is_valid():
        mobileotp = serializer.save()
        return Response({
            "message": "Mobile number is verified successfully.",
           "business_email": mobileotp.phone
        },status=status.HTTP_201_CREATED)
     
    return Response({
        "message": "Invalid Data",
        "errors": serializer.errors,
    },status=status.HTTP_400_BAD_REQUEST)        


@api_view(['POST'])
@permission_classes([])
def register_vendor(request):
     serializer = RegisterVendorSerializer(data=request.data)
     if serializer.is_valid():
          try:
               pass
            
          except Exception as e:
               return Response({
                    "message": "Unable to register at User level",
                    "errors": str(e)
               },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

          return Response({
               "message": "User is created."
          },status=status.HTTP_201_CREATED)
     
     return Response({
          "message": "Invalid Data",
          "errors": serializer.errors,
     },status=status.HTTP_400_BAD_REQUEST)
