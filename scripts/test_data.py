#!/usr/bin/env python
"""
Script to create test cart and favorites data
Run with: python manage.py shell < scripts/test_data.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneushop.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product
from cart.models import Cart, CartItem
from favorites.models import Favorite

User = get_user_model()

def create_test_data():
    """Create test cart and favorites data"""
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='test@pneushop.tn',
        defaults={
            'username': 'testuser',
            'is_verified': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created test user: {user.email}")
    
    # Get some products
    products = Product.objects.filter(is_active=True)[:5]
    
    if not products:
        print("No products found. Please run populate_products.py first.")
        return
    
    # Create cart and add items
    cart, created = Cart.objects.get_or_create(user=user)
    
    for i, product in enumerate(products[:3]):
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': i + 1}
        )
        if created:
            print(f"Added to cart: {product.name}")
    
    # Add favorites
    for product in products:
        favorite, created = Favorite.objects.get_or_create(
            user=user,
            product=product
        )
        if created:
            print(f"Added to favorites: {product.name}")
    
    print(f"\nTest data created for user: {user.email}")
    print(f"Cart items: {cart.total_items}")
    print(f"Favorites: {user.favorites.count()}")

if __name__ == '__main__':
    create_test_data()
