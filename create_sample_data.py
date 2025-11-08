#!/usr/bin/env python3
"""
Script to populate the database with sample tire data
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneushop.settings')
django.setup()

from products.models import Product, Category

def create_sample_data():
    # Create categories
    categories_data = [
        {
            'name': 'Pneus Voiture',
            'slug': 'pneus-voiture',
            'description': 'Pneus pour véhicules de tourisme'
        },
        {
            'name': 'Pneus Camionnette',
            'slug': 'pneus-camionnette',
            'description': 'Pneus pour camionnettes et véhicules utilitaires'
        },
        {
            'name': 'Pneus Camion',
            'slug': 'pneus-camion',
            'description': 'Pneus pour poids lourds et camions'
        },
        {
            'name': 'Pneus Agricole',
            'slug': 'pneus-agricole',
            'description': 'Pneus pour véhicules agricoles'
        }
    ]

    categories = {}
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        categories[cat_data['slug']] = category
        if created:
            print(f"✅ Created category: {category.name}")

    # Create sample products
    products_data = [
        # Car tires
        {
            'name': 'P Zero',
            'slug': 'pirelli-p-zero-225-45-r17',
            'description': 'Pneu haute performance pour véhicules sportifs. Excellent grip et tenue de route.',
            'price': Decimal('180.00'),
            'old_price': Decimal('220.00'),
            'category': categories['pneus-voiture'],
            'brand': 'Pirelli',
            'size': '225/45R17',
            'season': 'summer',
            'stock': 25,
            'is_featured': True,
        },
        {
            'name': 'EcoContact 6',
            'slug': 'continental-ecocontact-6-205-55-r16',
            'description': 'Pneu écologique avec une faible résistance au roulement.',
            'price': Decimal('145.00'),
            'category': categories['pneus-voiture'],
            'brand': 'Continental',
            'size': '205/55R16',
            'season': 'summer',
            'stock': 40,
            'is_featured': False,
        },
        {
            'name': 'CrossClimate 2',
            'slug': 'michelin-crossclimate-2-215-60-r17',
            'description': 'Pneu toutes saisons avec une excellente durabilité.',
            'price': Decimal('165.00'),
            'old_price': Decimal('185.00'),
            'category': categories['pneus-voiture'],
            'brand': 'Michelin',
            'size': '215/60R17',
            'season': 'all_season',
            'stock': 35,
            'is_featured': True,
        },
        {
            'name': 'WinterContact TS 860',
            'slug': 'continental-wintercontact-ts-860-195-65-r15',
            'description': 'Pneu hiver avec une adhérence exceptionnelle sur neige et verglas.',
            'price': Decimal('125.00'),
            'category': categories['pneus-voiture'],
            'brand': 'Continental',
            'size': '195/65R15',
            'season': 'winter',
            'stock': 20,
            'is_featured': False,
        },
        {
            'name': 'Primacy 4',
            'slug': 'michelin-primacy-4-225-50-r17',
            'description': 'Pneu premium pour berlines avec un confort de conduite optimal.',
            'price': Decimal('155.00'),
            'category': categories['pneus-voiture'],
            'brand': 'Michelin',
            'size': '225/50R17',
            'season': 'summer',
            'stock': 30,
            'is_featured': False,
        },
        
        # Van tires
        {
            'name': 'Agilis CrossClimate',
            'slug': 'michelin-agilis-crossclimate-215-65-r16c',
            'description': 'Pneu toutes saisons pour camionnettes avec une longévité exceptionnelle.',
            'price': Decimal('165.00'),
            'category': categories['pneus-camionnette'],
            'brand': 'Michelin',
            'size': '215/65R16C',
            'season': 'all_season',
            'stock': 15,
            'is_featured': True,
        },
        {
            'name': 'VancoContact 100',
            'slug': 'continental-vancocontact-100-205-75-r16c',
            'description': 'Pneu robuste pour véhicules utilitaires légers.',
            'price': Decimal('140.00'),
            'old_price': Decimal('160.00'),
            'category': categories['pneus-camionnette'],
            'brand': 'Continental',
            'size': '205/75R16C',
            'season': 'summer',
            'stock': 12,
            'is_featured': False,
        },
        
        # Truck tires
        {
            'name': 'XZE2+',
            'slug': 'michelin-xze2-plus-315-80-r22-5',
            'description': 'Pneu poids lourd pour essieu directeur avec une excellente kilométrage.',
            'price': Decimal('450.00'),
            'category': categories['pneus-camion'],
            'brand': 'Michelin',
            'size': '315/80R22.5',
            'season': 'all_season',
            'stock': 8,
            'is_featured': True,
        },
        {
            'name': 'Conti EcoPlus HD3',
            'slug': 'continental-ecoplus-hd3-295-80-r22-5',
            'description': 'Pneu économique pour transport longue distance.',
            'price': Decimal('380.00'),
            'old_price': Decimal('420.00'),
            'category': categories['pneus-camion'],
            'brand': 'Continental',
            'size': '295/80R22.5',
            'season': 'all_season',
            'stock': 6,
            'is_featured': False,
        },
        
        # Agricultural tires
        {
            'name': 'VF710/70R42 CerexBib 2',
            'slug': 'michelin-cerexbib-2-vf710-70-r42',
            'description': 'Pneu agricole haute technologie pour tracteurs modernes.',
            'price': Decimal('1250.00'),
            'category': categories['pneus-agricole'],
            'brand': 'Michelin',
            'size': 'VF710/70R42',
            'season': 'all_season',
            'stock': 4,
            'is_featured': True,
        },
        {
            'name': 'TractorMaster',
            'slug': 'continental-tractormaster-520-85-r38',
            'description': 'Pneu robuste pour machines agricoles lourdes.',
            'price': Decimal('890.00'),
            'old_price': Decimal('950.00'),
            'category': categories['pneus-agricole'],
            'brand': 'Continental',
            'size': '520/85R38',
            'season': 'all_season',
            'stock': 3,
            'is_featured': False,
        },
    ]

    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            slug=product_data['slug'],
            defaults=product_data
        )
        if created:
            print(f"✅ Created product: {product.brand} {product.name} - {product.size}")

    print(f"\n📊 Database populated with:")
    print(f"   - {Category.objects.count()} categories")
    print(f"   - {Product.objects.count()} products")
    print(f"   - {Product.objects.filter(is_featured=True).count()} featured products")
    print(f"   - {Product.objects.filter(stock__lt=10).count()} low stock products")

if __name__ == "__main__":
    try:
        create_sample_data()
        print("\n🎉 Sample data created successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()