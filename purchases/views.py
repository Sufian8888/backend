from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import PurchaseOrder, PurchaseOrderItem
from .serializers import (
    PurchaseOrderSerializer, 
    PurchaseOrderItemSerializer,
    PurchaseOrderCreateSerializer
)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders (buying from suppliers)
    """
    queryset = PurchaseOrder.objects.all().prefetch_related('items', 'supplier')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by supplier
        supplier = self.request.query_params.get('supplier', None)
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        
        # Filter by week and year
        week = self.request.query_params.get('week', None)
        year = self.request.query_params.get('year', None)
        if week:
            queryset = queryset.filter(week=week)
        if year:
            queryset = queryset.filter(year=year)
        
        return queryset.order_by('-order_date')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_order = serializer.save()
        
        # Return with full details using PurchaseOrderSerializer
        output_serializer = PurchaseOrderSerializer(purchase_order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a purchase order"""
        purchase_order = self.get_object()
        
        if purchase_order.status != 'draft':
            return Response(
                {'error': 'Only draft orders can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        purchase_order.status = 'confirmed'
        purchase_order.confirmed_date = timezone.now()
        purchase_order.save()
        
        serializer = self.get_serializer(purchase_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_received(self, request, pk=None):
        """Mark a purchase order as received"""
        purchase_order = self.get_object()
        
        if purchase_order.status != 'confirmed':
            return Response(
                {'error': 'Only confirmed orders can be marked as received'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        purchase_order.status = 'received'
        purchase_order.received_date = timezone.now()
        purchase_order.save()
        
        # Update product stock for each item
        for item in purchase_order.items.all():
            if item.product:
                # Use received_quantity if set, otherwise use ordered quantity
                qty_to_add = item.received_quantity if item.received_quantity > 0 else item.quantity
                item.product.stock += qty_to_add
                item.product.save()
        
        serializer = self.get_serializer(purchase_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a purchase order"""
        purchase_order = self.get_object()
        
        if purchase_order.status == 'received':
            return Response(
                {'error': 'Cannot cancel a received order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        purchase_order.status = 'cancelled'
        purchase_order.save()
        
        serializer = self.get_serializer(purchase_order)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get purchase order statistics"""
        total_orders = self.queryset.count()
        draft_orders = self.queryset.filter(status='draft').count()
        confirmed_orders = self.queryset.filter(status='confirmed').count()
        received_orders = self.queryset.filter(status='received').count()
        cancelled_orders = self.queryset.filter(status='cancelled').count()
        
        # Calculate total value
        total_value = sum(order.total for order in self.queryset.filter(status__in=['confirmed', 'received']))
        
        return Response({
            'total_orders': total_orders,
            'draft_orders': draft_orders,
            'confirmed_orders': confirmed_orders,
            'received_orders': received_orders,
            'cancelled_orders': cancelled_orders,
            'total_value': total_value
        })


class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase order items
    """
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by purchase order
        purchase_order = self.request.query_params.get('purchase_order', None)
        if purchase_order:
            queryset = queryset.filter(purchase_order_id=purchase_order)
        
        return queryset
