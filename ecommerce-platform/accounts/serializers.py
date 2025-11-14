from rest_framework import serializers
from .models import User,EmailOtp
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from django.conf import settings
from django.utils import timezone
import random

# Signup user With request email verification otp
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150,required=True)
    last_name = serializers.CharField(max_length=150,required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Password does not match.")
        return data
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value
    
    def create(self, validated_data):
        email = validated_data['email']
        otp = str(random.randint(100000,999999))
        # send email 
        try:
            send_mail(
                subject="Verify Email at ShopWaveX using OTP",
                message=f"your otp is {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
        except Exception as e:
            raise serializers.ValidationError("Unable to send mail. Please try again later")
        
        user_data = {
            "email": validated_data['email'],
            "first_name": validated_data['first_name'],
            "last_name": validated_data['last_name'],
            "is_verified": False
        }
        user = User.objects.create(**user_data)
        user.set_password(validated_data['confirm_password'])
        return user,otp

class RequestOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is not registered.")
        return value
    
        
    def create(self, validated_data):
        email = validated_data['email']
        otp = str(random.randint(100000,999999))
        # send email 
        try:
            send_mail(
                subject="Verify Email at ShopWaveX using OTP",
                message=f"your otp is {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
        except Exception as e:
            raise serializers.ValidationError("Unable to send mail. Please try again later")
        try:
            user = User.objects.get(email=validated_data['email'])
            # if user.is_verified:
            #     user.is_verified = False
        except User.DoesNotExist:
            raise serializers.ValidationError("Email does not exist.")
        
        return user,otp
        
# this does not work proper. because model's field changed.
class EmailVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    # def validate_email(self, value):
    #     if EmailOtp.objects.filter(email=value, isVerified=True).exists():
    #         raise serializers.ValidationError("Email is already verified.")
    #     elif not EmailOtp.objects.filter(email=value).exists():
    #         raise serializers.ValidationError("Email does not exist.")
    #     return value
    # def validate_otp(self, value):
    #     if len(value) == 6:
    #         raise serializers.ValidationError("Please Enter Vaild OTP.")
    #     return value
    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
            self.user = user
            emailotp =EmailOtp.objects.get(user=user)
            self.emailotp = emailotp
        except User.DoesNotExist:
            raise serializers.ValidationError("Email does not exist.")
        except EmailOtp.DoesNotExist:
            raise serializers.ValidationError("Email does not exist to verify.")
        
        if emailotp.isUsed:
            raise serializers.ValidationError("OTP is used before.")
        if emailotp.isExpire(5):
            raise serializers.ValidationError("OTP is Expired. Please use resend otp api.")
        if emailotp.otp != data['otp']:
            raise serializers.ValidationError("Please Enter a Valid OTP.")
        return data
        
    def create(self, validated_data):
        # user = User.objects.get(email=validated_data['email'])
        self.user.is_verified = True
        self.user.save()
        self.emailotp.isUsed = True
        return self.user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Email does not exist.")
        
        if not user.is_verified:
            raise serializers.ValidationError("email is not verified.Please verify first.")
        if not user.is_active:
            raise serializers.ValidationError(" not active user.")
        # if user.role == 'vendor':
        #     raise serializers.ValidationError("User not Found.")
        
        # check user credentials
        user = authenticate(email=data['email'],password=data['password']) # this in inbuilt authentication backend. For Custom, go through Alumni project

        if not user:
            raise serializers.ValidationError("Invaild Credentials")
        
        user.last_login = timezone.now()
        user.save()
        # generate token
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user":{
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }

class logoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self,data):
        self.token = data['refresh_token']
        user = self.context['request'].user

        try:
            token = RefreshToken(self.token)
            # if token.payload.get("user_id") != user.id:  # need to know details
            #     raise serializers.ValidationError("Token does not belong to the authenticate user.")
        except TokenError:
            raise serializers.ValidationError("Invaild or expired Token.")

        return data
    
    def save(self,**kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError("Unable to blacklist the token")


class forgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self,data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Password must match Confirm Password.")
        try:
            user = User.objects.get(email=data['email'])
            self.user = user # strore class instace variable
            if not user.is_verified:
                raise serializers.ValidationError("Please verify email using otp.")
            # enforced to verify using otp first
            emailotp = EmailOtp.objects.get(user=user)
            self.emailotp = emailotp
            if emailotp.isExpire(10):
                raise serializers.ValidationError("Time Expired. First verify your email using otp.")
            
            if emailotp.otp != data['otp']:
                raise serializers.ValidationError("Please Enter valid otp.")
            
            if emailotp.isUsed:
                raise serializers.ValidationError("This otp is already used.")

        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        except EmailOtp.DoesNotExist:
            raise serializers.ValidationError("otp instance is not found.")
        return data
    
    def save(self,**kwargs):
        try:
            self.user.set_password(self.validated_data['password'])
            self.user.save()
            self.emailotp.isUsed = True
            self.emailotp.save()
        except:
            raise serializers.ValidationError("Unable to change the password")
        return self.user


    

        
        