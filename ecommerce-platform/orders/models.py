from django.db import models,transaction
from django.db.models import F
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from accounts.models import User
from products.models import ProductVariant
from vendors.models import Vendor


# Create your models here.

def generate_order_number():
    #order number can be improoved in future for specific purpose
    return uuid.uuid4().hex.upper()

class Order(models.Model):

    # order statuses 
    STATUS_CHOICES = [
        ("PLACED","Placed"),
        ("CONFIRMED","Confirmed"),
        ("PROCESSING", "Processing"),
        ("PACKED", "Packed"),
        ("SHIPPED", "Shipped"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
        ("RETURN_REQUESTED", "Return Requested"),
        ("RETRUNED", "Returned"),
        ("REFUNDED", "Refunded"),
        ("CLOSED", "Closed"),
    ]

    PAYMENT_CHOICES = [
        ("PAYMENT_PENDING","Pending"),
        ("PAYMENT_PAID", "Paid"),
        ("PAYEMENT_FAILED", "Failed"),
        ("PAYMENT_REFUNDED", "Refunded"),
    ]
    id = models.BigAutoField(primary_key=True)
    order_number = models.CharField(max_length=64, unique=True, db_index=True,default=generate_order_number)
    customer = models.ForeignKey(User,on_delete=models.PROTECT,related_name='orders')

    #shipping snapshot
    shipping_name = models.CharField(max_length=200)
    shipping_phone= models.CharField(max_length=12)
    shipping_email = models.EmailField(blank=True, null=True)
    shipping_address_1= models.CharField(max_length=255)
    shipping_address_2 = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_pincode = models.CharField(max_length=12)

    
    #monetary snapshots
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_charge = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_CHOICES,default="PAYMENT_PENDING")
    payment_reference = models.CharField(max_length=255,blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="PROCESSING")

    is_refundable = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["customer","created_at"]),
        ]

    def __str__(self):
        return f"Order {self.order_number} ({self.customer.email})"
    
    def compute_totals(self,tax=0.00,shipping_charge=0.00,discount=0.00):
        # computing total
        items = self.items.all()
        sub_total = sum((i.price*i.quantity) for i in items)
        self.subtotal = Decimal(sub_total)

        self.tax = Decimal(tax)
        self.shipping_charge = Decimal(shipping_charge)
        self.discount = Decimal(discount)
        self.total = self.subtotal + self.tax + self.shipping_charge - self.discount

        self.save(update_fields=["subtotal", "tax", "shipping_charge", "total", "updated_at"])
        return self.total
    
    @classmethod
    def create_order(cls, customer, items, shipping_snapshot: dict, payment_method=None, payment_reference=None,status="PROCESSING",
                     payment_status="PAYMENT_PENDING"):
        # items must be list of dicts
        # shipping address must be dict
        if not items:
            raise ValidationError("No items provided for order creation.")
        
        if not shipping_snapshot:
            raise ValidationError("No Shipping details is provided.")
        
        with transaction.atomic():
            order = cls.objects.create(
                customer=customer,
                shipping_name=shipping_snapshot.get('shipping_name'),
                shipping_phone=shipping_snapshot.get('shipping_phone'),
                shipping_email = shipping_snapshot.get('shipping_email'),
                shipping_address_1 = shipping_snapshot.get('shipping_address_1'),
                shipping_address_2 = shipping_snapshot.get('shipping_address_2'),
                shipping_city = shipping_snapshot.get('shipping_city'),
                shipping_state = shipping_snapshot.get('shipping_state'),
                shipping_pincode=shipping_snapshot.get('shipping_pincode'),
                payment_method=payment_method,
                payment_reference=payment_reference,
                status=status,
                payment_status=payment_status
                
            )

        total_calc = Decimal("0.00")

        for it in items:
            variant_id = it.get("item_id")
            qty = int(it.get('qty',1)) # default 1

            if qty <= 0:
                raise ValidationError("Quantity must be Positive integer.")
            
            # lock the variant row for update to avoid race condition
            try:
                variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
            except ProductVariant.DoesNotExist:
                raise ValidationError(f"Variant {variant_id} does not exist.")
            
            # this does not hold good when product.is_deleted = False, but we
            # can apply here user "or variant.product.is_deleted" but we left for now
            if not variant.is_active or variant.is_deleted:
                raise ValidationError(f"Variant {variant_id} is not saleable.")
            
            if variant.stock < qty:
                raise ValidationError(f"Insufficient stock for variant {variant.sku} (requested {qty}, available {variant.stock}).")
            
            price = variant.adjusted_price if variant.adjusted_price is not None else variant.product.base_price
            try:
                vendor = Vendor.objects.get(owner=variant.product.vendor)
            except Vendor.DoesNotExist:
                raise ValidationError(f"Vendor not found.")
            # create item
            OrderItem.objects.create(
                    order=order,
                    product_variant=variant,
                    vendor=vendor,
                    quantity=qty,
                    price=price,
                    tax_amount=Decimal("0.00"),
                    commission_amount=Decimal("0.00"),
                    vendor_earning=(Decimal(price)*qty),
            )
            # Reduce stock and save variant
            variant.stock = F("stock") - qty # to preserve Concurrency safety
            variant.save(update_fields=["stock"])
            # To get the latest value from db
            variant.refresh_from_db()

            total_calc += (Decimal(price)*qty)

        
        order.subtotal = total_calc
        order.total = total_calc + order.tax + order.shipping_charge - order.discount
        order.save(update_fields=["subtotal", "tax", "shipping_charge", "discount", "total"])

        return order
    
    def set_status(self, new_status: str, by_user=None):
        """
        Set Order-level status and record timestamps for close/deliver events.
        """

        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError("Invalid status")
        
        self.status = new_status

        if new_status == "DELIVERED":
            self.closed_at = timezone.now()
        if new_status in ("CANCELLED","REFUNDED","CLOSED"):
            self.closed_at = timezone.now()

        self.save(update_fields=["status", "closed_at", "updated_at"])
        return self
    
    def can_be_cancelled(self):
        # order can be cancelled before it is packed/shipped/delivered
        return self.status in {"PLACED","CONFIRMED","PROCESSING"}
    
    


class OrderItem(models.Model):
    """
    Each item in an order represents  one product variant purchased from a vendor.OrderItem tracks its own lifecycle
    becuase  each item may be fullfilled separately (multi-vendor, split-shipments)
    """
    ITEM_STATUS_CHOICE = [
        ("PENDING", "Pending"),
        ("CONFIRMED","Confirmed"),
        ("PACKED", "Packed"),
        ("SHIPPED", "Shipped"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
        ("RETURN_REQUESTED", "Return Requested"),
        ("RETRUNED", "Returned"),
        ("REFUNDED", "Refunded"),
        ("CLOSED", "Closed"),
    ]

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="order_items")
    vendor = models.ForeignKey(Vendor,on_delete=models.PROTECT, related_name='order_items')

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12,decimal_places=2,default=Decimal("0.00"))

    #per-item financials used for settlement
    tax_amount = models.DecimalField(max_digits=5,decimal_places=2,default=Decimal("0.00"))
    commission_amount = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal("0.00"))
    vendor_earning = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    refunded_amount = models.DecimalField(max_digits=12,decimal_places=2,default=Decimal("0.00"))

    #tracking
    status = models.CharField(max_length=32, choices=ITEM_STATUS_CHOICE, default="PENDING")
    tracking_number = models.CharField(max_length=128, blank=True, null=True)
    courier_name = models.CharField(max_length=128, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True) # e.g. picking notes, return reason

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["order","vendor"]),
            models.Index(fields=["product_variant", "status"]),
        ]

    def __str__(self):
        return f"{self.product_variant.sku} x {self.quantity} ({self.order.order_number})"
    
    # override the parent class mehtod
    def save(self, *args, **kwargs):
        self.subtotal = (Decimal(self.price) * self.quantity)
        self.vendor_earning = self.subtotal - self.commission_amount - self.tax_amount
        super().save(*args, **kwargs)

    
    def set_status(self, new_status: str):
        if new_status not in dict(self.ITEM_STATUS_CHOICE):
            raise ValueError("Invalid item status")
        self.status = new_status
        if new_status == "DELIVERED":
            self.delivered_at = timezone.now()
        self.save(update_fields=["status", "delivered_at", "updated_at"])


    def initiate_return(self, reason: str, requester: User,):

        if self.status != "DELIVERED":
            raise ValidationError("Return can not be initiated at this item status")
        
        self.status = "RETURN_REQUESTED"

        # store reason in metadata
        meta = self.metadata or {}
        meta.setdefault("return_requests",[]).append({
            "requested_by": requester.id,
            "reason": reason,
            "requested_at": timezone.now().isoformat()
        })
        self.metadata = meta
        self.save(update_fields=["status", "metadata", "updated_at"])




class CheckoutSession(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAYMENT_INITIATED", "Payment Initiated"),
        ("PAID", "Paid"),
        ("EXPIRED", "Expired"),
        ("CANCELLED", "Cancelled",)
    ]

    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    customer = models.ForeignKey(User,on_delete=models.CASCADE, related_name="checkout_sessions")
    payload = models.JSONField() #store items, shipping_snapshot, metadata

    amount = models.DecimalField(max_digits=12, decimal_places=2,default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PENDING')
    payment_gateway_order_id = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self,t=15):
        return timezone.now()  > (self.created_at) + timezone.timedelta(minutes=t)
    
    def mark_payment_initiated(self,gateway_order_id):
        self.payment_gateway_order_id = gateway_order_id
        self.status = "PAYMENT_INITIATED"
        self.save(update_fields=["payment_gateway_order_id","status"])
    def __str__(self):
        return f"{self.customer.email} checkout {self.status}"




