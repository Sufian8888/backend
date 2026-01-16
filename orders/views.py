# from rest_framework import generics, permissions, viewsets
# from .models import Delivery, Order, PurchaseOrder
# from .serializers import DeliverySerializer, OrderSerializer, PurchaseOrderSerializer
# from rest_framework.permissions import IsAuthenticated

# class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Order.objects.all()
#     serializer_class = OrderSerializer
#     permission_classes = [permissions.AllowAny]


# class OrderListCreateView(generics.ListCreateAPIView):
#     serializer_class = OrderSerializer
#     # queryset = Order.objects.all().order_by('-created_at')

#     permission_classes = [permissions.IsAuthenticated]

#     # def get_queryset(self):
#     #     # Admins see all orders, normal users only see theirs
#     #     user = self.request.user
#     #     if user.is_staff or user.is_superuser:
#     #         return Order.objects.all().order_by('-created_at')
#     #     return Order.objects.filter(user=user).order_by('-created_at')
#     def get_queryset(self):
#     # Admins see all orders, normal users only see theirs
#         user = self.request.user
#         if user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'sales':
#             queryset = Order.objects.all().order_by('-created_at')
#         else:
#             queryset = Order.objects.filter(user=user).order_by('-created_at')
        
#         # Filter by status if provided
#         status = self.request.query_params.get('status', None)
#         if status:
#             queryset = queryset.filter(status=status)
        
#         return queryset
#     def perform_create(self, serializer):
#         # Generate order number if not provided
#         order = serializer.save(user=self.request.user)
#         if not order.order_number:
#             order.order_number = f'PN-{order.id:06d}'
#             order.save()
        
#         # Generate tracking number
#         if not order.tracking_number:
#             order.tracking_number = f'TRK-{order.id:06d}'
#             order.save()



# class PurchaseOrderViewSet(viewsets.ModelViewSet):
#     queryset = PurchaseOrder.objects.all().order_by("-date_commande")
#     serializer_class = PurchaseOrderSerializer



# class DeliveryViewSet(viewsets.ModelViewSet):
#     queryset = Delivery.objects.all()
#     serializer_class = DeliverySerializer
#     permission_classes = [IsAuthenticated]


from rest_framework import generics, permissions, viewsets
from .models import Delivery, Order, PurchaseOrder
from .serializers import DeliverySerializer, OrderSerializer, PurchaseOrderSerializer
from rest_framework.permissions import IsAuthenticated

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all().prefetch_related("items").select_related("user")
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin, superuser, or sales can see all
        if user.is_staff or user.is_superuser or getattr(user, "role", "") == "sales":
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(user=user)

        # Add optimization for related models
        queryset = queryset.prefetch_related("items").select_related("user").order_by("-created_at")

        # Optional: Filter by status
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def perform_create(self, serializer):
        from django.utils import timezone
        from products.models import Product
        from django.db import transaction
        from accounts.email_utils import send_order_confirmation_email
        
        with transaction.atomic():
            order = serializer.save(user=self.request.user)
            
            # Subtract stock for each order item
            for item_data in order.items.all():
                if item_data.product_id:
                    try:
                        product = Product.objects.select_for_update().get(id=item_data.product_id)
                        print(f"[ORDER CREATE] Product: {product.name}, Stock before: {product.stock}, Ordered: {item_data.quantity}")
                        
                        if product.stock >= item_data.quantity:
                            product.stock -= item_data.quantity
                            product.save()
                            print(f"[ORDER CREATE] Stock after: {product.stock}")
                        else:
                            print(f"[ORDER CREATE] WARNING: Insufficient stock for {product.name}. Available: {product.stock}, Ordered: {item_data.quantity}")
                    except Product.DoesNotExist:
                        print(f"[ORDER CREATE] WARNING: Product ID {item_data.product_id} not found")
            
            if not order.order_number:
                year = timezone.now().strftime('%y')  # Get 2-digit year
                # Get the count of orders created this year
                year_start = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                order_count = Order.objects.filter(created_at__gte=year_start).count()
                order.order_number = f"PS{year}{order_count:06d}"
                order.save()

            if not order.tracking_number:
                order.tracking_number = f"TRK-{order.id:06d}"
                order.save()
            
            # Send order confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                print(f"[ORDER CREATE] Failed to send confirmation email: {str(e)}")


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by("-date_commande")
    serializer_class = PurchaseOrderSerializer


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
