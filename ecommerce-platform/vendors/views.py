# from django.shortcuts import render, redirect
# from django.http import JsonResponse
# from accounts.models import Customer
# from .serializers import CustomerSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes,authentication_classes
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .serializers import (VendorRegisterOTPSerializer,VendorVerifyOTPSerializer,
                          VendorRegisterMobileOtpSerializer,VerifyMobileOTPSerializer,
                          VendorDocumentSerializer,PickUpAddressSerializer,
                          RegisterVendorSerializer,VendorLoginSerializer)
from .models import (Vendor,VendorEmailOtp,VendorMobileOtp,VendorID,PickUpAddress)
from ecommerce_platform.utils import generate_otp
from .utils.on_board_token import create_vendor_step_token,verify_vendor_step_token
from .authentication import VendorStepAuthentication
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from django.utils import timezone
from .permissions import IsOnVerdingVendor
User = get_user_model()

@api_view(['POST'])
@permission_classes([])
def vendor_register_email_otp(request):
    serializer = VendorRegisterOTPSerializer(data=request.data)
    if serializer.is_valid():
        business_email = serializer.validated_data.get('business_email')

        if User.objects.filter(email=business_email,role='customer',is_verified=True).exists():
             return Response({
                  "message": "Email alreday exist as a customer."
             },status=status.HTTP_400_BAD_REQUEST)
        

        otp = generate_otp()
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
                    "message": "Unable to send email"
               },status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            # print("Jai Shree Ram")
            # print(token)
            # print(otp)
            # print(business_email)

          #   VendorEmailOtp.objects.create(
          #        business_email=serializer.validated_data.get('business_email'),
          #        otp=otp,
          #        isUsed=False,
          #        is_verified=False
          #   )
            VendorEmailOtp.objects.update_or_create(
                business_email=serializer.validated_data.get('business_email'),
                defaults={"otp": otp,
                          "isUsed": False,
                          "is_verified": False}
           )                 
            token = create_vendor_step_token(serializer.validated_data.get('business_email'),5)
            # VendorAccessToken.objects.update_or_create(
            #      business_email= email_otp_obj,
            #      defaults={
            #           "access_token": token
            #      }
            # )
        except Exception as e:
            return Response({
                "error": "Unable to process otp request.",
                "message": str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "message": "OTP sent successfully. Check your email.",
            "access_token": token
        },status=status.HTTP_200_OK)
    
    return Response({
        "message": "Invaild Data",
        "error": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
@authentication_classes([VendorStepAuthentication])
def vendor_verify_email_otp(request):

    token = request.auth
    if not token:
         return Response({
              "message": "Token is not provided."
         },status=401)
    
    email_in_token = token.get('field')
 
    serializer = VendorVerifyOTPSerializer(data=request.data, context = {
         "email_in_token": email_in_token
    })

    if serializer.is_valid():
        business_email = serializer.validated_data.get('business_email')
        emailotp = serializer.save()
        token = create_vendor_step_token(business_email,5)
        return Response({
           "message": "Email is verified successfully.",
           "acess_token": token
        },status=status.HTTP_201_CREATED)
 
    return Response({
          "message": "Invalid Data",
          "errors": serializer.errors,
     },status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([])
@authentication_classes([VendorStepAuthentication])
def vendor_register_mobile_otp(request):
     
     token = request.auth
     if not token:
          return Response({
               "message": "Token is not provided"
          },status=401)
     
     email_in_token = token.get("field")
     serializer = VendorRegisterMobileOtpSerializer(data=request.data, context={
          "email_in_token": email_in_token
     })
     # serializer = VendorRegisterMobileOtpSerializer(data=request.data)

     if serializer.is_valid():

        phone = serializer.validated_data.get('phone')
        business_email = serializer.validated_data.get("business_email")
        otp = generate_otp() #6 digit

        try:
            VendorMobileOtp.objects.update_or_create(
                 phone=phone,
                 business_email=business_email,
                 defaults={
                      "otp": otp,
                      "isUsed": False,
                      "is_verified": False
                 }
            )
          #   VendorMobileOtp.objects.create(
          #       phone=phone,
          #       business_email=business_email,
          #       otp=otp,
          #       isUsed= False,
          #       is_verified=False
          #   )

            
               # Send This Otp to the mobile number using api.
            token = create_vendor_step_token(phone,5)

        except Exception as e:
                print(str(e))
                return Response({
                    "message": "Unable to process mobile otp.",
               },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
          
        return Response({
               "message": "Sorry,Unable to send otp on mobile number. contact admin.",
               "access_token": token
          },status=status.HTTP_200_OK)
     

     return Response({
               "message": "Invalid Data",
               "error": serializer.errors
          },status=status.HTTP_400_BAD_REQUEST)


     
@api_view(['POST'])
@permission_classes([])
@authentication_classes([VendorStepAuthentication])
def vendor_verify_mobile_otp(request):
    token = request.auth
    if not token:
         return Response({
              "message": "token is not provided"
         },status=400)
    
    phone_in_token = token.get('field')
    serializer = VerifyMobileOTPSerializer(data=request.data,context={
         "phone_in_token": phone_in_token
    })
    if serializer.is_valid():
        mobileotp = serializer.save()
        if not mobileotp:
             return Response({
                  "message": "Unable to proceed otp"
             },status=500)
        
        token = create_vendor_step_token(mobileotp.phone,5)
        return Response({
            "message": "Mobile number is verified successfully.",
             "access_token": token
        },status=status.HTTP_201_CREATED)
     
    return Response({
        "message": "Invalid Data",
        "errors": serializer.errors,
    },status=status.HTTP_400_BAD_REQUEST)        


@api_view(['POST'])
@permission_classes([])
@authentication_classes([VendorStepAuthentication])
def register_vendor(request):
     token = request.auth
     if not token:
          return Response({
               "message": "Token is not provided"
          },status=401)
     
     phone_in_token = token.get("field")
     serializer = RegisterVendorSerializer(data=request.data, context={
          "phone_in_token": phone_in_token
     })

     # serializer = RegisterVendorSerializer(data=request.data)

     if serializer.is_valid():
          business_email = serializer.validated_data.get('business_email')
          phone = serializer.validated_data.get('phone')
          password = serializer.validated_data.get('password')
          confirm_password = serializer.validated_data.get('confirm_password')
          try:
               vendor = User.objects.create(
                    email = business_email,
                    is_verified = True,
                    role = 'vendor'
               )
               vendor.set_password(password)
               vendor.save()
          except Exception as e:
               return Response({
                    "message": "Unable to save user as a vendor",
                    "erros": str(e),
               },status=500)
          
          try:
               Vendor.objects.create(
                    owner=vendor,
                    business_email=business_email,
                    phone=phone,
                    is_completed=False,
                    status='DRAFT'
               )
          except Exception as e:
               return Response({
                    "message": "Unable to save vendor",
                    "errors": str(e),
               },status=500)
          
          refresh = RefreshToken.for_user(vendor)
          return Response({
               "message": "Vendro registered Successfully.",
               "refresh": str(refresh),
               "access": str(refresh.access_token),
          },status=status.HTTP_201_CREATED)
     
     return Response({
          "message": "Invalid Data",
          "errors": serializer.errors,
     },status=status.HTTP_400_BAD_REQUEST)
     
     
@api_view(['POST'])
@permission_classes([])
def vendor_login(request):
     serializer = VendorLoginSerializer(data=request.data)
     if serializer.is_valid():
          business_email = serializer.validated_data.get('business_email')
          password = serializer.validated_data.get('password')
          try:
               vendor = User.objects.get(email=business_email,role='vendor',
                                         is_verified=True,is_active=True)

          except User.DoesNotExist:
               return Response({
                    "message": "Email does not exist."
               },status=404)
          

          vendor = authenticate(email=business_email,password=password)

          if not vendor:
               return Response({
                    "message": "Invalid Credential"
               },status=400)
          
          vendor_obj = getattr(vendor,'vendor',None)

          if not vendor_obj: # This will raise if directly create user as a vendor
               return Response({
                    "message": "Vendor Class is not defined."
               },status=500)
          
          if vendor_obj.status in ['REJECTED','SUSPENDED']:
               return Response({
                    "message": f"Vendor is {vendor_obj.status}"
               },status = 400)
          
          
          vendor.last_login = timezone.now()
          vendor.save()

          #generate token
          refresh = RefreshToken.for_user(vendor)
          return Response({
               "message": "Logged in Successfully.",
               "refresh": str(refresh),
               "access": str(refresh.access_token),
               "vendor": {
                    "id": vendor.id,
                    "business_email": vendor_obj.business_email,
                    "full_name":  vendor_obj.full_name,
                    "seller_name": vendor_obj.seller_name,
                    "status": vendor_obj.status,
                    "onboarding_complete": vendor_obj.is_completed
               }
          },status=status.HTTP_200_OK)
     
     return Response({
          "message": "Invalid Data",
          'errors': serializer.errors
     },status=status.HTTP_400_BAD_REQUEST)
          
          

     








# this is compulsary part when api key got.
def gst_verify_by_gov_api(request):
     pass

@api_view(['POST'])
@permission_classes([IsOnVerdingVendor])
def upload_vendor_doc(request):
     # token = request.auth
     # if not token:
     #      return Response({
     #           "message": "Token is not provided"
     #      },status=400)
     
     # mobile_no_in_token = token.get("field")
     # serializer = VendorDocumentSerializer(data=request.data,context={
     #      "mobile_no_in_token": mobile_no_in_token
     # })
     serializer = VendorDocumentSerializer(data=request.data)
     if serializer.is_valid():
          # email = serializer.validated_data.get('business_email')
          # phone = serializer.validated_data.get('phone')
          user = request.user
          full_name = serializer.validated_data.get('full_name')
          seller_name = serializer.validated_data.get('seller_name')
          gst = serializer.validated_data.get('gst')
          signeture = serializer.validated_data.get('signeture')
          gst_img = serializer.validated_data.get('gst_img')
          alt_text_signeture = f"{seller_name}-image"
          alt_text_gst_certificate = f"{gst}-image"
          try:
               vendor_obj = getattr(user,"vendor",None)
               if not vendor_obj:
                    return Response({
                         "message": "Unable to set seller name and full name",
                    },status=500)
               
               vendor_obj.full_name = full_name
               vendor_obj.seller_name = seller_name
               vendor_obj.save()
          except Exception as e:
               return Response({
                    "message": "Unable to set fullname and seller name",
                    "errors": str(e)
               },status=500)

          try:
               VendorID.objects.update_or_create(
                    vendor = vendor_obj,
                    gst=gst,
                    defaults={
                         "signeture":signeture,
                         "alt_text_signeture":alt_text_signeture,
                         "gst_certificate": gst_img,
                         "alt_text_gst_certificate": alt_text_gst_certificate,
                         "verified_at_user_level": False,
                         "verified_by_admin": False,
                    }
               )

               # token = create_vendor_step_token(gst,5)

          except Exception as e:
               return Response({
                    "message": "Unable to save document.",
                    "error": str(e)
               },status=500)
          
          return Response({
               "message": "Document uploaded successfully.",
          },status=201)


     return Response({
          "message": "Invalid data",
          "errors": serializer.errors
     },status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
# @authentication_classes([VendorStepAuthentication])
def add_pickup_address(request):
     # token = request.auth
     # if not token:
     #      return Response({
     #           "message": "Token is not provided"
     #      },status=400)
     
     # gst_in_token = token.get("field")
     # gst_in_token = "27ABCDE1234F2Z5"
     # serializer = PickUpAddressSerializer(data=request.data,context={
     #      "gst_in_token": gst_in_token
     # })
     serializer = PickUpAddressSerializer(data=request.data)
     if serializer.is_valid():
          user = request.user
          vendor_obj = getattr(user,"vendor",None)
          if not vendor_obj:
               return Response({
                    "message": "Unable to set seller name and full name",
               },status=500)
          # business_email = serializer.validated_data.get("business_email")
          try:
               PickUpAddress.objects.update_or_create(
                    vendor = vendor_obj,
                    defaults={
                         "address_line_1": serializer.validated_data.get('address_line_1'),
                         "address_line_2": serializer.validated_data.get('address_line_2'),
                         "city": serializer.validated_data.get("city"),
                         "state": serializer.validated_data.get("state"),
                         "pincode": serializer.validated_data.get('pincode')
                    }

               )
               # token = create_vendor_step_token(business_email.business_email,5)
          except Exception as e:
               return Response({
                    "message": "Unable to proceed pickup addres.",
                    "errors": str(e),
               },status=500)
          
          return Response({
               "message": "Address is saved successfully.",
               # "token": token
          },status=status.HTTP_200_OK)
     

     return Response({
          "message": "Invalid Data",
          "errors": serializer.errors,
     },status=status.HTTP_400_BAD_REQUEST)

 






# @api_view(['POST'])
# @permission_classes([])
# def register_vendor(request):
#      serializer = PickUpAddressSerializer(data=request.data)
#      if serializer.is_valid():
#           try:
#                pass
            
#           except Exception as e:
#                return Response({
#                     "message": "Unable to register at User level",
#                     "errors": str(e)
#                },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#           return Response({
#                "message": "User is created."
#           },status=status.HTTP_201_CREATED)
     
#      return Response({
#           "message": "Invalid Data",
#           "errors": serializer.errors,
#      },status=status.HTTP_400_BAD_REQUEST)
