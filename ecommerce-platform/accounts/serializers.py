from rest_framework import serializers
from .models import User,EmailOtp
from django.core.mail import send_mail
from django.conf import settings
import random

# Signup user With request email verification otp
class EmailOtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    f_name = serializers.CharField(max_length=150,required=True)
    l_name = serializers.CharField(max_length=150,required=True)
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
        
        # model instance created
        email_otp = EmailOtp.objects.update_or_create(email=validated_data['email'],
                                            defaults={"otp": otp})
        user_data = {
            "email": validated_data['email'],
            "first_name": validated_data['f_name'],
            "last_name": validated_data['l_name'],
            "is_verified": False
        }
        user = User.objects.create(**user_data)
        user.set_password(validated_data['confirm_password'])
        user.save()
        return user

class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is not registered.")
    
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
        
        email_otp = EmailOtp.objects.update_or_create(email=validated_data['email'],
                                            defaults={"otp": otp})
        return email_otp
        

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
            record = EmailOtp.objects.get(email=data['email'])
        except EmailOtp.DoesNotExist:
            raise serializers.ValidationError("Email does not exist to verify.")
        
        if record.isExpire():
            record.delete()
            raise serializers.ValidationError("OTP is Expired. Please Enter Email Again.")
        if record.otp != data['otp']:
            raise serializers.ValidationError("Please Enter a Valid OTP.")
        return data
        
    def create(self, validated_data):
        record = EmailOtp.objects.get(email=validated_data['email'])
        record.is_verified = True
        record.save()
        return record


        

