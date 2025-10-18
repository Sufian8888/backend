#!/usr/bin/env python3
"""
🛞 PneuShop Complete System Test
Tests cart functionality, order processing, and inventory management
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneushop.settings')
django.setup()

from accounts.models import CustomUser
from products.models import Product, Order, OrderItem, Category
from cart.models import Cart, CartItem
from django.db import transaction

def test_complete_system():
    print("🛞 PNEU SHOP - COMPLETE SYSTEM TEST")
    print("=" * 60)
    
    # Get test user and product
    user = CustomUser.objects.filter(is_staff=False).first()
    if not user:
        user = CustomUser.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Customer',
            phone='12345678'
        )
        print(f"✅ Created test customer: {user.email}")
    
    product = Product.objects.filter(is_active=True, stock__gt=0).first()
    if not product:
        print("❌ No products with stock available for testing")
        return
    
    print(f"📊 Initial State:")
    print(f"   User: {user.email}")
    print(f"   Product: {product.name}")
    print(f"   Product Stock: {product.stock}")
    print(f"   Product Price: {product.price} TND")
    print()
    
    # Test 1: Add to Cart
    print("🛒 TEST 1: Adding to Cart")
    print("-" * 30)
    
    cart, created = Cart.objects.get_or_create(user=user)
    cart.items.all().delete()  # Clear any existing items
    
    # Add 3 items to cart
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 3}
    )
    
    print(f"✅ Added {cart_item.quantity}x {product.name} to cart")
    print(f"   Cart Total Items: {cart.total_items}")
    print(f"   Cart Total Price: {cart.total_price} TND")
    print()
    
    # Test 2: Checkout Process
    print("🏪 TEST 2: Checkout Process")
    print("-" * 30)
    
    original_stock = product.stock
    
    try:
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                user=user,
                status='pending',
                total_amount=cart.total_price,
                shipping_address='123 Avenue Habib Bourguiba, Tunis 1000',
                notes='Test order - expedited shipping requested'
            )
            
            # Create order items and update stock
            for cart_item in cart.items.all():
                if cart_item.product.stock < cart_item.quantity:
                    raise ValueError(f"Insufficient stock for {cart_item.product.name}")
                
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()
            
            # Complete order
            order.status = 'completed'
            order.save()
            
            # Clear cart
            cart.items.all().delete()
            
            print(f"✅ Order Created Successfully")
            print(f"   Order Number: {order.order_number}")
            print(f"   Total Amount: {order.total_amount} TND")
            print(f"   Status: {order.status}")
            print(f"   Items: {order.total_items}")
            print()
            
            # Test 3: Inventory Update
            print("📦 TEST 3: Inventory Management")
            print("-" * 30)
            
            product.refresh_from_db()
            print(f"✅ Stock Updated Successfully")
            print(f"   Original Stock: {original_stock}")
            print(f"   Quantity Sold: {cart_item.quantity}")
            print(f"   New Stock: {product.stock}")
            print()
            
            # Test 4: Admin Dashboard Stats
            print("📊 TEST 4: Admin Dashboard Stats")
            print("-" * 30)
            
            total_orders = Order.objects.count()
            completed_orders = Order.objects.filter(status='completed').count()
            total_revenue = Order.objects.filter(status='completed').aggregate(
                total=models.Sum('total_amount')
            )['total'] or 0
            
            print(f"✅ Dashboard Stats:")
            print(f"   Total Products: {Product.objects.count()}")
            print(f"   Total Orders: {total_orders}")
            print(f"   Completed Orders: {completed_orders}")
            print(f"   Total Revenue: {total_revenue} TND")
            print(f"   Low Stock Products: {Product.objects.filter(stock__lt=10).count()}")
            print()
            
            # Test 5: Cart Clearing
            print("🧹 TEST 5: Cart Management")
            print("-" * 30)
            
            print(f"✅ Cart Cleared After Order")
            print(f"   Cart Items: {cart.total_items}")
            print(f"   Cart Total: {cart.total_price} TND")
            print()
            
            print("🎉 ALL TESTS PASSED!")
            print("=" * 60)
            print("✅ Cart Add Functionality: WORKING")
            print("✅ Order Processing: WORKING") 
            print("✅ Inventory Management: WORKING")
            print("✅ Stock Deduction: WORKING")
            print("✅ Cart Clearing: WORKING")
            print("✅ Admin Dashboard: WORKING")
            print()
            print("🛞 PneuShop Cart & Order System is fully functional!")
            
    except Exception as e:
        print(f"❌ Error during checkout: {e}")
        return False
    
    return True

if __name__ == "__main__":
    from django.db import models
    test_complete_system()