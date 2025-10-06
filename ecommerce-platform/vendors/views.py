# from django.shortcuts import render, redirect
# from django.http import JsonResponse
# from accounts.models import Customer
# from .serializers import CustomerSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
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