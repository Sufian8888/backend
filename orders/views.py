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
        order = serializer.save(user=self.request.user)
        if not order.order_number:
            order.order_number = f"PN-{order.id:06d}"
            order.save()

        if not order.tracking_number:
            order.tracking_number = f"TRK-{order.id:06d}"
            order.save()


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by("-date_commande")
    serializer_class = PurchaseOrderSerializer


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
