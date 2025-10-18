#!/usr/bin/env python
"""
Script to populate the database with sample products
Run with: python manage.py shell < scripts/populate_products.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneushop.settings')
django.setup()

from products.models import Category, Product
from django.utils.text import slugify

def create_categories():
    """Create product categories"""
    categories_data = [
        {
            'name': 'Pneus Voiture',
            'description': 'Pneus pour véhicules légers et voitures particulières'
        },
        {
            'name': 'Pneus SUV/4x4',
            'description': 'Pneus pour SUV, 4x4 et véhicules tout-terrain'
        },
        {
            'name': 'Pneus Camionnette',
            'description': 'Pneus pour camionnettes et véhicules utilitaires'
        },
        {
            'name': 'Pneus Moto',
            'description': 'Pneus pour motos et scooters'
        }
    ]
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'slug': slugify(cat_data['name']),
                'description': cat_data['description']
            }
        )
        if created:
            print(f"Créé catégorie: {category.name}")

def create_products():
    """Create sample products"""
    # Get categories
    voiture = Category.objects.get(name='Pneus Voiture')
    suv = Category.objects.get(name='Pneus SUV/4x4')
    
    products_data = [
        # Pneus Voiture
        {
            'name': 'EcoContact 6',
            'brand': 'Continental',
            'size': '205/55R16',
            'category': voiture,
            'price': 89.99,
            'old_price': 109.99,
            'season': 'summer',
            'stock': 25,
            'is_featured': True,
            'description': 'Pneu été haute performance avec excellente adhérence et faible résistance au roulement.'
        },
        {
            'name': 'Primacy 4',
            'brand': 'Michelin',
            'size': '215/60R17',
            'category': voiture,
            'price': 125.50,
            'season': 'summer',
            'stock': 18,
            'is_featured': True,
            'description': 'Pneu premium offrant sécurité et longévité exceptionnelles.'
        },
        {
            'name': 'Turanza T005',
            'brand': 'Bridgestone',
            'size': '225/45R18',
            'category': voiture,
            'price': 145.00,
            'old_price': 165.00,
            'season': 'summer',
            'stock': 12,
            'is_featured': False,
            'description': 'Pneu sport touring pour une conduite dynamique et confortable.'
        },
        {
            'name': 'WinterContact TS 860',
            'brand': 'Continental',
            'size': '205/55R16',
            'category': voiture,
            'price': 95.99,
            'season': 'winter',
            'stock': 30,
            'is_featured': True,
            'description': 'Pneu hiver avec technologie avancée pour une sécurité optimale.'
        },
        {
            'name': 'Alpin 6',
            'brand': 'Michelin',
            'size': '215/60R17',
            'category': voiture,
            'price': 135.00,
            'season': 'winter',
            'stock': 22,
            'is_featured': False,
            'description': 'Pneu hiver haute performance pour conditions difficiles.'
        },
        {
            'name': 'CrossClimate 2',
            'brand': 'Michelin',
            'size': '205/55R16',
            'category': voiture,
            'price': 115.99,
            'old_price': 135.99,
            'season': 'all_season',
            'stock': 35,
            'is_featured': True,
            'description': 'Pneu toutes saisons révolutionnaire, été comme hiver.'
        },
        
        # Pneus SUV
        {
            'name': 'Latitude Sport 3',
            'brand': 'Michelin',
            'size': '235/60R18',
            'category': suv,
            'price': 165.00,
            'season': 'summer',
            'stock': 15,
            'is_featured': True,
            'description': 'Pneu SUV sport pour performances exceptionnelles sur route.'
        },
        {
            'name': 'ContiCrossContact LX2',
            'brand': 'Continental',
            'size': '225/65R17',
            'category': suv,
            'price': 145.50,
            'old_price': 170.00,
            'season': 'all_season',
            'stock': 20,
            'is_featured': False,
            'description': 'Pneu SUV polyvalent pour route et léger tout-terrain.'
        },
        {
            'name': 'Dueler H/P Sport',
            'brand': 'Bridgestone',
            'size': '255/55R19',
            'category': suv,
            'price': 185.99,
            'season': 'summer',
            'stock': 8,
            'is_featured': True,
            'description': 'Pneu SUV premium pour véhicules haut de gamme.'
        },
        {
            'name': 'Grabber GT',
            'brand': 'General Tire',
            'size': '235/60R18',
            'category': suv,
            'price': 125.00,
            'season': 'summer',
            'stock': 25,
            'is_featured': False,
            'description': 'Pneu SUV économique avec bonnes performances.'
        }
    ]
    
    for product_data in products_data:
        slug = slugify(f"{product_data['brand']}-{product_data['name']}-{product_data['size']}")
        
        product, created = Product.objects.get_or_create(
            slug=slug,
            defaults=product_data
        )
        
        if created:
            print(f"Créé produit: {product.brand} {product.name} {product.size}")

def main():
    print("Création des catégories...")
    create_categories()
    
    print("\nCréation des produits...")
    create_products()
    
    print(f"\nTerminé! {Category.objects.count()} catégories et {Product.objects.count()} produits créés.")

if __name__ == '__main__':
    main()
