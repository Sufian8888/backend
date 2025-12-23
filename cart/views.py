from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Cart, CartItem
from .serializers import CartSerializer
from products.models import Product

class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        # Prevent caching of cart data
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    try:
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not product_id:
            return Response({'error': 'product_id est requis'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        if quantity <= 0:
            return Response({'error': 'La quantité doit être positive'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Log initial state
        print(f"[ADD TO CART] Product: {product.name} (ID: {product.id}), Initial Stock: {product.stock}, Quantity to add: {quantity}")
        
        # Check stock availability
        if product.stock < quantity:
            return Response({'error': f'Stock insuffisant. Disponible: {product.stock}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        with transaction.atomic():
            # Refresh product to get latest stock
            product.refresh_from_db()
            
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not item_created:
                # When item already exists in cart, just check if we can add MORE
                print(f"[ADD TO CART] Item exists in cart with quantity: {cart_item.quantity}")
                if product.stock < quantity:
                    return Response({'error': f'Stock insuffisant. Disponible: {product.stock}'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                cart_item.quantity += quantity
                cart_item.save()
                print(f"[ADD TO CART] Updated cart quantity to: {cart_item.quantity}")
            else:
                print(f"[ADD TO CART] Created new cart item with quantity: {quantity}")
            
            # Subtract stock immediately when adding to cart
            old_stock = product.stock
            product.stock -= quantity
            product.save()
            print(f"[ADD TO CART] Stock updated: {old_stock} -> {product.stock}")
        
        # Refresh to get updated stock
        product.refresh_from_db()
        
        response = Response({
            'message': 'Produit ajouté au panier',
            'cart': CartSerializer(cart).data,
            'item_id': cart_item.id,
            'updated_product': {
                'id': product.id,
                'stock': product.stock
            }
        })
        # Prevent caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.data.get('quantity', 1))
    
    print(f"[UPDATE CART] Item ID: {item_id}, Product: {cart_item.product.name}, Old Qty: {cart_item.quantity}, New Qty: {quantity}")
    
    with transaction.atomic():
        old_quantity = cart_item.quantity
        
        if quantity <= 0:
            # Restore stock when deleting item
            cart_item.product.stock += old_quantity
            cart_item.product.save()
            cart = cart_item.cart
            cart_item.delete()
            message = 'Produit supprimé du panier'
            return Response({
                'message': message,
                'cart': CartSerializer(cart).data
            })
        else:
            # Calculate difference in quantity
            quantity_diff = quantity - old_quantity
            
            print(f"[UPDATE CART] Stock before: {cart_item.product.stock}, Qty diff: {quantity_diff}")
            
            # Check stock availability for increase
            if quantity_diff > 0 and cart_item.product.stock < quantity_diff:
                return Response({'error': f'Stock insuffisant. Disponible: {cart_item.product.stock}'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Update stock: subtract if increasing, add back if decreasing
            cart_item.product.stock -= quantity_diff
            cart_item.product.save()
            
            print(f"[UPDATE CART] Stock after: {cart_item.product.stock}")
            
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Quantité mise à jour'
    
    # Refresh to get updated stock
    cart_item.product.refresh_from_db()
    
    response = Response({
        'message': message,
        'cart': CartSerializer(cart_item.cart).data,
        'updated_product': {
            'id': cart_item.product.id,
            'stock': cart_item.product.stock
        }
    })
    # Prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart
    
    product_id = cart_item.product.id
    
    with transaction.atomic():
        # Restore stock when removing from cart
        cart_item.product.stock += cart_item.quantity
        cart_item.product.save()
        # Get updated stock before deleting
        updated_stock = cart_item.product.stock
        cart_item.delete()
    
    response = Response({
        'message': 'Produit supprimé du panier',
        'cart': CartSerializer(cart).data,
        'updated_product': {
            'id': product_id,
            'stock': updated_stock
        }
    })
    # Prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from user's cart"""
    cart = get_object_or_404(Cart, user=request.user)
    
    # Check if we should restore stock (default: yes, unless clearing after checkout)
    restore_stock = request.query_params.get('restore_stock', 'true').lower() == 'true'
    
    with transaction.atomic():
        if restore_stock:
            # Restore stock for all items before clearing (user manually cleared cart)
            print(f"[CLEAR CART] Restoring stock for {cart.items.count()} items")
            for cart_item in cart.items.all():
                cart_item.product.stock += cart_item.quantity
                cart_item.product.save()
                print(f"[CLEAR CART] Restored {cart_item.quantity} to {cart_item.product.name}")
        else:
            # Don't restore stock (cart cleared after checkout)
            print(f"[CLEAR CART] NOT restoring stock (checkout completed)")
        
        cart.items.all().delete()
    
    return Response({
        'message': 'Panier vidé',
        'cart': CartSerializer(cart).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_cart(request):
    """Process cart checkout and create order without payment"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        
        if not cart.items.exists():
            return Response({'error': 'Le panier est vide'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get shipping address from request
        shipping_address = request.data.get('shipping_address', '')
        notes = request.data.get('notes', '')
        
        # Import Order models here to avoid circular imports
        from django.apps import apps
        Order = apps.get_model('products', 'Order')
        OrderItem = apps.get_model('products', 'OrderItem')
        
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                user=request.user,
                status='pending',
                total_amount=cart.total_price,
                shipping_address=shipping_address,
                notes=notes
            )
            
            # Create order items (stock already subtracted when added to cart)
            for cart_item in cart.items.all():
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                
                # Note: Stock was already subtracted when item was added to cart
                # No need to subtract again here
            
            # Clear cart after successful order WITHOUT restoring stock
            print(f"[CHECKOUT] Clearing cart without restoring stock")
            cart.items.all().delete()
            
            # Complete the order (skip payment processing)
            order.status = 'completed'
            order.save()
            
            from django.utils import timezone
            year = timezone.now().strftime('%y')
            year_start = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            from django.apps import apps
            Order = apps.get_model('products', 'Order')
            order_count = Order.objects.filter(created_at__gte=year_start).count()
            order_number = f'PS{year}{order_count:06d}'
            
            return Response({
                'message': 'Commande créée avec succès',
                'order_id': order.id,
                'order_number': order_number,
                'total_amount': float(order.total_amount),
                'status': order.status
            })
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
