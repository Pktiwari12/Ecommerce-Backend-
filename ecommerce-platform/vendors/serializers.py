from rest_framework import serializers
from accounts.models import User
from .models import Vendor,VendorEmailOtp,VendorMobileOtp
import re

class VendorRegisterOTPSerializer(serializers.Serializer):
    business_email = serializers.EmailField(required=True)

    def validate_business_email(self,value):
        if Vendor.objects.filter(business_email=value,is_completed=True).exists():
            raise serializers.ValidationError("Email already exists.")
        return value


class VendorVerifyOTPSerializer(serializers.Serializer):
    business_email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)

    def validate_business_email(self,value):
        if Vendor.objects.filter(business_email=value,is_completed=True).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value
        
    def validate(self,data):
        try:
            print(data.get("business_email"))
            if len(data.get('otp')) != 6:
                raise serializers.ValidationError("Invaild OTP.")

            emailotp = VendorEmailOtp.objects.get(business_email=data.get('business_email'))
            self.emailotp = emailotp
            if emailotp.otp != data.get('otp'):
                raise serializers.ValidationError("OTP is not vaild.")
            if emailotp.isUsed:
                raise serializers.ValidationError("OTP is used before.")
            if emailotp.isExpire(5):
                raise serializers.ValidationError("OTP is Expired.")
        except VendorEmailOtp.DoesNotExist:
            raise serializers.ValidationError("Enter correct email id to verify otp.")
        
        return data
    
    def create(self,validated_data):
        self.emailotp.isUsed = True
        self.emailotp.is_verified = True
        self.emailotp.save()
        return self.emailotp


class MobileOtpRequestSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(required=True)

    def validate_mobile_number(self,value):
        print(value)
        if len(value) != 10:
            raise serializers.ValidationError("only ten digits allowed.")
        
        if not value.isdigit():
            raise serializers.ValidationError("Mobile no. must have only numeric value")
        
        if ' ' in value or '\t' in value or '\n' in value:
            raise serializers.ValidationError("Invalid mobile number.")
        
        if Vendor.objects.filter(phone=value,is_completed=True).exists():
            raise serializers.ValidationError("Mobile number already exists.")
        
        return value

class VerifyMobileOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)

    def validate_mobile_number(self,value):
        print(value)
        if len(value) != 10:
            raise serializers.ValidationError("only ten digits allowed.")
        
        if not value.isdigit():
            raise serializers.ValidationError("Mobile no. must have only numeric value")
        
        if ' ' in value or '\t' in value or '\n' in value:
            raise serializers.ValidationError("Invalid mobile number.")
        
        if Vendor.objects.filter(phone=value,is_completed=True).exists():
            raise serializers.ValidationError("Mobile number already exists.")
        
        return value
        
    def validate(self,data):
        try:
            # print(data.get("business_email"))
            if len(data.get('otp')) != 6:
                raise serializers.ValidationError("Invaild OTP.")

            mobileotp = VendorMobileOtp.objects.get(phone=data.get('mobile_number'))
            self.mobileotp = mobileotp
            if mobileotp.otp != data.get('otp'):
                raise serializers.ValidationError("OTP is not vaild.")
            if mobileotp.isUsed:
                raise serializers.ValidationError("OTP is used before.")
            if mobileotp.isExpire(5):
                raise serializers.ValidationError("OTP is Expired.")
        except VendorMobileOtp.DoesNotExist:
            raise serializers.ValidationError("Enter correct mobile number to verify otp.")
        
        return data
    
    def create(self,validated_data):
        self.mobileotp.isUsed = True
        self.mobileotp.is_verified = True
        self.mobileotp.save()
        return self.mobileotp
        

class PickUpAddressSerializer(serializers.Serializer):
    address_line_1 = serializers.CharField(required=True)
    address_line_2 = serializers.CharField(required=False)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True)
    is_primary = serializers.BooleanField(required=True)

class RegisterVendorSerializer(serializers.Serializer):
    business_email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    seller_name = serializers.CharField(required=True)
    gst = serializers.CharField(required=True)
    # password = serializers.CharField(required=True)
    # confirm_password = serializers.CharField(required=True)

    def validate_business_email(self,value):
        if Vendor.objects.filter(business_email=value,is_completed=True).exists():
            raise serializers.ValidationError("Email id is already exists.")
        if not VendorEmailOtp.objects.filter(business_email=value).exists():
            raise serializers.ValidationError("Email id not verified.")
        return value
    
    def validate_phone(self,value):
        print(value)
        if len(value) != 10:
            raise serializers.ValidationError("only ten digits allowed.")
        
        if not value.isdigit():
            raise serializers.ValidationError("Mobile no. must have only numeric value")
        
        if ' ' in value or '\t' in value or '\n' in value:
            raise serializers.ValidationError("Invalid mobile number.")
        
        if Vendor.objects.filter(phone=value,is_completed=True).exists():
            raise serializers.ValidationError("Mobile number already exists.")
        
        if not VendorMobileOtp.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Mobile no. is not verified.")
        return value
    
    def validate_gst(self,value):
        gst_pattern = r"^([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$)"

        if not re.match(gst_pattern,value):
            raise serializers.ValidationError("Invalid GSTIN fromat.")
        
        if Vendor.objects.filter(gst=value,is_completed=True).exists():
            raise serializers.ValidationError("User already registered with gst number.")
        return value
    
    # def validate(self,data):
    #     strong_password = (
    #         r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#_\-])[A-Za-z\d@$!%*?&#_\-]{8,15}$'
    #     )
    #     if not re.match(strong_password,data.get('password')):
    #         raise serializers.ValidationError("Use Strong Password.")
        
    #     if data.get('password') != data.get('confirm_password'):
    #         raise serializers.ValidationError("password and confirm_password must be same.")
        
    #     return data
        

        
    

        
        


