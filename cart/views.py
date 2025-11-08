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
        
        # Check stock availability
        if product.stock < quantity:
            return Response({'error': f'Stock insuffisant. Disponible: {product.stock}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        with transaction.atomic():
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                new_quantity = cart_item.quantity + quantity
                if product.stock < new_quantity:
                    return Response({'error': f'Stock insuffisant. Disponible: {product.stock}'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                cart_item.quantity = new_quantity
                cart_item.save()
        
        return Response({
            'message': 'Produit ajouté au panier',
            'cart': CartSerializer(cart).data,
            'item_id': cart_item.id
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.data.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        message = 'Produit supprimé du panier'
    else:
        # Check stock availability
        if cart_item.product.stock < quantity:
            return Response({'error': f'Stock insuffisant. Disponible: {cart_item.product.stock}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        message = 'Quantité mise à jour'
    
    return Response({
        'message': message,
        'cart': CartSerializer(cart_item.cart).data
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart
    cart_item.delete()
    
    return Response({
        'message': 'Produit supprimé du panier',
        'cart': CartSerializer(cart).data
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from user's cart"""
    cart = get_object_or_404(Cart, user=request.user)
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
            
            # Create order items and update stock
            for cart_item in cart.items.all():
                # Check if enough stock is available
                if cart_item.product.stock < cart_item.quantity:
                    return Response({
                        'error': f'Stock insuffisant pour {cart_item.product.name}. Disponible: {cart_item.product.stock}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()
            
            # Clear cart after successful order
            cart.items.all().delete()
            
            # Complete the order (skip payment processing)
            order.status = 'completed'
            order.save()
            
            return Response({
                'message': 'Commande créée avec succès',
                'order_id': order.id,
                'order_number': f'PN-{order.id:06d}',
                'total_amount': float(order.total_amount),
                'status': order.status
            })
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
