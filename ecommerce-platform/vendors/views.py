# from django.shortcuts import render, redirect
# from django.http import JsonResponse
# from accounts.models import Customer
# from .serializers import CustomerSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import VendorRegistrationSerializer
# Create your views here.

# manually serialization 


# def sign_up(request):
#     # vendors = {
#     #     'id': 1,
#     #     'name': "Saching",
#     #     'loc' : "Mumbai"
#     # }
#     vendors = Customer.objects.all()
#     print(vendors)
#     vendors = list(vendors.values()) # manually serialization
#     return JsonResponse(vendors, safe=False)


# using rest framework serializer
# @api_view(['GET'])
# def sign_up(request):
#     if request.method == 'GET':
#         # Get all the data from the Customer Table
#         vendors = Customer.objects.all()
#         serializer = CustomerSerializer(vendors,many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)






@api_view(['POST'])
def register_vendor(request):
    """
    Vendor registration view (Function-based)
    """

    serializer = VendorRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        vendor = serializer.save()
        return Response({
            "message": "Vendor registered successfully.",
            "vendor": {
                "email": vendor.owner.email,
                "full_name": vendor.owner.first_name,
                "seller_name": vendor.seller_name,
                "status": vendor.status
            }
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
