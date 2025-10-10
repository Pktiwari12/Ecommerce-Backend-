from rest_framework import serializers
from .models import EmailOtp
from django.core.mail import send_mail
from django.conf import settings
import random
class EmailOtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if EmailOtp.objects.filter(email=value, is_verified=True).exists():
            raise serializers.ValidationError("Email already registered.")
        return value
    
    def create(self, validated_data):
        email = validated_data['email']
        otp = str(random.randint(100000,999999))
        # model instance created
        email_otp = EmailOtp.objects.update_or_create(email=email,
                                                      defaults={'otp': otp})
        
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


        

