# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from .serializers import RegisterSerializer,EmailVerifySerializer,RequestOtpSerializer,LoginSerializer,logoutSerializer,forgotPasswordSerializer
from .models import EmailOtp
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAuthenticated
# Create your views here.
@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user,otp = serializer.save()  # triggers create or update method of serializer
        try:
            
            user.save() # instance saved into db
            EmailOtp.objects.update_or_create(user=user,
                                            defaults={"otp": otp,
                                                      "isUsed": False})
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
@permission_classes([])
def request_otp(request):
    serializer = RequestOtpSerializer(data=request.data)
    if serializer.is_valid():
        user,otp = serializer.save()
        try:
            email_otp = EmailOtp.objects.update_or_create(user=user,
                                                          defaults={"otp": otp,
                                                                    "isUsed": False})
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
        "error": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)

# this does not work proper. because model's field changed.
@api_view(['POST'])
def email_verify(request):
    serializer = EmailVerifySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Email is verified successfully."
        },status=status.HTTP_201_CREATED)
     
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            "message": "Logged in Successfully",
            "data": serializer.validated_data
        },status=status.HTTP_200_OK)
    
    return Response({
        "message": "Invaild Data",
        "errors": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    serializer = logoutSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "User logged out successfully",
            "data": {
                "id": request.user.id,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email
            }
        },status= status.HTTP_205_RESET_CONTENT)
    
    return Response({
        "errors": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['PUT'])
@permission_classes([])
def forgot_password(request):
    serializer = forgotPasswordSerializer(data=request.data)
    if(serializer.is_valid()):
        user = serializer.save()
        return Response({
            "message": "Password changed Successfully.",
            "data": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            }
        },status=status.HTTP_200_OK)
    else:
        return Response({
            "error": serializer.errors,
        },status=status.HTTP_400_BAD_REQUEST)
