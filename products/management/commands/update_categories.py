from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = 'Update categories to match new requirements'

    def handle(self, *args, **options):
        # New categories structure
        new_categories = [
            {
                'name': 'Agricole',
                'slug': 'agricole',
                'description': 'Pneus pour véhicules agricoles'
            },
            {
                'name': '4x4',
                'slug': '4x4',
                'description': 'Pneus pour véhicules 4x4 et SUV'
            },
            {
                'name': 'Moto',
                'slug': 'moto',
                'description': 'Pneus pour motos et scooters'
            },
            {
                'name': 'Tourisme',
                'slug': 'tourisme',
                'description': 'Pneus pour véhicules de tourisme'
            },
            {
                'name': 'Utilitaire',
                'slug': 'utilitaire',
                'description': 'Pneus pour véhicules utilitaires et camionnettes'
            }
        ]

        self.stdout.write(self.style.WARNING('Updating categories...'))
        
        # Mapping old slugs to new slugs for product migration
        slug_mapping = {
            'pneus-voiture': 'auto',
            'pneus-camionnette': 'utilitaire',
            'pneus-camion': 'utilitaire',
            'pneus-agricole': 'agricole',
            'pneus-suv': '4x4',
            'pneus-moto': 'moto',
        }

        # Create or update new categories
        for cat_data in new_categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created category: {category.name}'))
            else:
                # Update existing category
                category.name = cat_data['name']
                category.description = cat_data['description']
                category.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Updated category: {category.name}'))

        # Migrate products from old categories to new ones
        from products.models import Product
        
        for old_slug, new_slug in slug_mapping.items():
            try:
                old_category = Category.objects.get(slug=old_slug)
                new_category = Category.objects.get(slug=new_slug)
                
                # Count products to migrate
                product_count = Product.objects.filter(category=old_category).count()
                
                if product_count > 0:
                    # Update products
                    Product.objects.filter(category=old_category).update(category=new_category)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Migrated {product_count} products from "{old_category.name}" to "{new_category.name}"'
                        )
                    )
                
                # Delete old category
                old_category.delete()
                self.stdout.write(self.style.WARNING(f'✗ Deleted old category: {old_slug}'))
                
            except Category.DoesNotExist:
                continue

        # Show final count
        total_categories = Category.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Complete! Total categories: {total_categories}')
        )
        
        # List all categories
        self.stdout.write('\nCurrent categories:')
        for cat in Category.objects.all().order_by('name'):
            product_count = cat.products.count()
            self.stdout.write(f'  • {cat.name} ({cat.slug}) - {product_count} products')
