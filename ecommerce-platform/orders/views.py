# from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import (ValidateItemSerializer,CheckoutValidateSerializer,InitiatePaymentSerializer,
                          CreateCodSerializer)
from products.models import ProductVariant
from .models import CheckoutSession,Order,OrderItem
from django.conf import settings
from decimal import Decimal

import hmac
import hashlib
import json

# item_level calculation
"""
According to business point of view , there are many price calculation ways. so by discussion, they will
be implemented.
"""
def compute_total(items_level_total_payment, price, qty, tax=Decimal("0.00"), discount=Decimal(0.00), shipping_charge=Decimal(0.00)):
    subtotal = Decimal(price) * qty
    total = subtotal - subtotal * discount
    total = total + total*tax
    total +=  shipping_charge

    items_level_total_payment['total'] += total
    items_level_total_payment['subtotal'] += subtotal
    return items_level_total_payment


# check items with it's available stock to buy
@api_view(['POST'])
@permission_classes([])
def validate_items(request):
    serializer = ValidateItemSerializer(data=request.data)

    if serializer.is_valid():
        items_with_qty = serializer.validated_data.get('items_with_qty')
        for iwq in items_with_qty:
            item_id = iwq.get('item_id')
            qty = iwq.get('qty')

            # get product from db
            try:
                variant = ProductVariant.objects.get(pk=item_id)
            except ProductVariant.DoesNotExist:
                return Response({
                    "message": f"Item(id={item_id})not found ",
                    "flag": False
                },status=404)
            
            # only active items is allowed
            if not variant.is_active or variant.is_deleted:
                return Response({
                    "message": f"Item(id={item_id})not found ",
                    "flag": False
                },status=404)
            # requested quantity is not greater than available stock.
            if variant.stock < qty:
                return Response({
                    "message": f"Insufficient stock for item(id={item_id},requested {qty} but available {variant.stock})",
                    "flag": False
                },status=422)   

        # Order can be proceeded further
        return Response({
            "message": "Order can be proceeded further.",
            "flag": True,
            "data": items_with_qty
        },status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_checkout(request):
    serializer = CheckoutValidateSerializer(data=request.data)
    # To pass 
    items_level_total_payment = {
        "total": Decimal("0.00"),
        "subtotal": Decimal("0.00")
    }

    if serializer.is_valid():
        items_with_qty = serializer.validated_data.get('items_with_qty')

        for iwq in items_with_qty:
            item_id = iwq.get('item_id')
            qty = iwq.get('qty')

            # get product from db
            try:
                variant = ProductVariant.objects.get(pk=item_id)
            except ProductVariant.DoesNotExist:
                return Response({
                    "message": f"Item(id={item_id})not found ",
                    "flag": False
                },status=404)
            
            # only active items is allowed
            if not variant.is_active or variant.is_deleted:
                return Response({
                    "message": f"Item(id={item_id})not found ",
                    "flag": False
                },status=404)
            # requested quantity is not greater than available stock.
            if variant.stock < qty:
                return Response({
                    "message": f"Insufficient stock for item(id={item_id},requested {qty} but available {variant.stock})",
                    "flag": False
                },status=422)

            compute_total(
                items_level_total_payment=items_level_total_payment,
                price=variant.adjusted_price,
                qty=qty, 
            )
        try:
            session = CheckoutSession.objects.create(
                customer=request.user,
                payload={
                    "items": items_with_qty,
                    "shipping": {
                        "shipping_name": serializer.validated_data.get("shipping_name"),
                        "shipping_phone": serializer.validated_data.get("shipping_phone"),
                        "shipping_email": serializer.validated_data.get("shipping_email"),
                        "shipping_address_1": serializer.validated_data.get("shipping_address_1"),
                        "shipping_address_2": serializer.validated_data.get("shipping_address_2"),
                        "shipping_city": serializer.validated_data.get("shipping_city"),
                        "shipping_state": serializer.validated_data.get("shipping_state"),
                        "shipping_pincode": serializer.validated_data.get("shipping_pincode") 
                    },
                    "payment_method": serializer.validated_data.get("payment_method"),
                },
                amount=Decimal(items_level_total_payment.get('total')),
                currency="INR"
            )

        except Exception as e:
            print(e)
            return Response({
                'message': "Unable to validate checkout",
            },status=500)

        # Order can be proceeded further
        return Response({
            "checkout_session_id": str(session.id),
            "ammount": items_level_total_payment.get('total'),
            "currency": "INR",
            "expiry_time": "15 min"
        },status=status.HTTP_200_OK)


    # request data failed validation 
    return Response({
        "message": "Invalid Data",
        "flag": False,
        "errors": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    serializer = InitiatePaymentSerializer(data=request.data)
    
    if serializer.is_valid():
        session_id = serializer.validated_data.get('checkout_session_id')
        try:
            session = CheckoutSession.objects.get(pk=session_id,customer=request.user)
        except CheckoutSession.DoesNotExist:
            return Response({
                "message": "Session not found.",
            },status=404)

        if session.is_expired(15):
            session.status = "EXPIRED"
            session.save(update_fields=['status'])
            return Response({
                "message": "Session is Expired.",
            },status=400)
        
        client = settings.RAZORPAY_CLIENT
        payable_amout = int(session.amount * 100)
        payload = {
            "amount": payable_amout,
            "currency": session.currency,
            "receipt": str(session.id),
            "partial_payment":False,
            "notes": {
                "platform": "website",
                "customer_id": str(request.user.id) 
            }
        }
        try:
            order = client.order.create(payload)
        except Exception as e:
            return Response({
                "message": "Razorpay error while make order.",
                "errors": str(e)
            },status=500)
        
        # store payment order_id
        session.mark_payment_initiated(order.get('id'))
        # session.status = "PAYMENT_INITIATED",
        # session.payment_gateway_order_id = order.get('id')
        # session.save(update_fields=['status','payment_gateway_order_id'])

        return Response({
            "message": "Payment is initiated.",
            "payment_gateway_id": order.get('id'),
            "razorpay_key": settings.KEY_ID,
            "amount": session.amount,
            "currency": session.currency,
        },status=200)
    

    return Response({
        "message": "Invalid data",
        "errors": serializer.errors,
    },status=400)



# # public api opened for razorpay payment confirmation
# @api_view(['POST'])
# @permission_classes([])
# def razorpay_webhook(request):
#     print("razorpay_called..")
#     payload = request.body
#     signeture = request.headers.get("X-Razorpay-Signature") or request.META.get("HTTP_X_RAZORPAY_SIGNATURE")
#     if not signeture:
#         print("signeture not found")
#         return Response({
#             "message": "signetrue not found"
#         },status=500)
#     print("signeture found.")
#     print(signeture)

#     return Response({
#         "message": "Webhook called",
#     },status=200)


@api_view(['POST'])
@permission_classes([])
def razorpay_webhook(request):
    """
    events : payment.captured, payment.authorized, payment.failed
    """
    payload = request.body
    signeture = request.headers.get("X-Razorpay-Signature") or request.META.get("HTTP_X_RAZORPAY_SIGNATURE")
    print(payload)
    if not signeture:
        return Response({
            "message": "Signeture missing"
        },status=400)
    print("signeture is found.")
    webhook_secret = settings.WEBHOOK_SECRET.encode()
    generated_signeture = hmac.new(webhook_secret,payload,hashlib.sha256).hexdigest()

    if not hmac.compare_digest(generated_signeture,signeture):
        print("invalid signeture")
        return Response({
            "message": "Invalid Signetrue"
        },status=400)
    print("Singeture is valid")

    try:
        event = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return Response({
            "message": "Invalid payload"
        },status=400)
    
    event_type = event.get("event")
    payment_entity = event.get("payload",{}).get("payment",{}).get("entity",{})
    razor_order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")
    payment_status = payment_entity.get("status")

    # find CheckoutSession
    try:
        session = CheckoutSession.objects.get(payment_gateway_order_id=razor_order_id)
    except CheckoutSession.DoesNotExist:
        return Response({
            "message": "Checkout session is not found",
        },status=404)
    
    # to avoid idempotency 
    if session.status == "PAID" and event_type in ["payment.captured", "payment.authorized"]:
        return Response({
            "message": "Already processed"
        },status=200)
    
    if event_type in ["payment.captured", "payment.authorized"]:
        payload_data = session.payload
        customer = session.customer
        items = payload_data.get('items')
        print(items)
        shipping = payload_data['shipping']
        # payment_method = payload_data.get("payment_method", "Online_Mode")
        payment_method = "Online_Mode"
        try:
            order = Order.create_order(
                customer=customer,
                items=items,
                shipping_snapshot=shipping,
                payment_method=payment_method,
                payment_reference=session.payment_gateway_order_id,
                status="CONFIRMED",
                payment_status="PAYMENT_PAID"
            )

        except Exception as e:
            print(str(e))
            session.status = "PAID"
            session.save(update_fields=["status"])
            return Response({
                "message": "Unable to create order.your payment will be refunded",
            },status=500)
        
        session.status = "PAID"
        session.save(update_fields=["status"])


        return Response({
            "message": "Order is created successfully.",
            "order_number": order.order_number
        },status=201)
    
    elif event_type == "payment.failed":
        session.status = "FAILED"
        session.save(update_fields=["status"])
        print("Payment is failed.")
        return Response({
            "message": "Payment Failed",
        },status=200)

    
    print(f"{event_type} is ignored.")
    return Response({
        "message": f"Event {event_type} ignored",
    },status=200)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order_cod(request):
    serializer = CreateCodSerializer(data=request.data)
    if serializer.is_valid():
        session_id = serializer.validated_data.get('checkout_session_id')
        try:
            session = CheckoutSession.objects.get(pk=session_id,customer=request.user)
        except CheckoutSession.DoesNotExist:
            return Response({
                "message": "Session not found.",
            },status=404)

        if session.is_expired(15):
            session.status = "EXPIRED"
            session.save(update_fields=['status'])
            return Response({
                "message": "Session is Expired.",
            },status=400)
        
        payload_data = session.payload
        customer = session.customer
        items = payload_data.get('items')
        shipping = payload_data.get('shipping')
        # payment_method = payload_data.get("payment_method","Cash_On_Delivery")
        payment_method = "Cash_On_Delivery"

        try:
            order = Order.create_order(
                customer=customer,
                items=items,
                shipping_snapshot=shipping,
                payment_method=payment_method,
                status="PROCESSING",
                payment_status="PAYMENT_PENDING"   
            )
        except Exception as e:
            return Response({
                "message": "Unable to create order."
            },status=500)
        
        return Response({
            "message": "Order is created sucessfully.",
            "order_number": order.order_number
        },status=201)
    
    return Response({
        "message": "Invalid data"
    },status=400)













# @api_view(['POST'])
# @permission_classes([])
# def create_order(request):
    
#     serializer = CreateOrderSerializer(data=request.data)
#     if serializer.is_valid():
#         # checkout 
#         data = {
#                 "amount": 1*100,
#                 "currency": "INR",
#                 "receipt": "Test Receipt 1",
#                 "partial_payment":False,
#                 "notes": {
#                             "name": "User",
#                             "platform": "website"
#                     }
#                 }
#         client = settings.RAZORPAY_CLIENT
#         key_id = settings.KEY_ID
#         key_secret = settings.KEY_SECRET
#         order = client.order.create(data)
#         print(order)
#         print(settings.KEY_ID)
#         return Response({
#             "order_id": order.get('id'),
#             "message": "Items is ordered succesfully."
#         },status=200)
    
#     return Response({
#         "message": "Invalid Data",
#         "errors": serializer.errors
#     },status=status.HTTP_400_BAD_REQUEST)




    


