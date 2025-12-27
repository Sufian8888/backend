from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category


class Command(BaseCommand):
    help = 'Create default product categories'

    def handle(self, *args, **kwargs):
        categories = [
            {
                'name': 'tourisme',
                'slug': 'tourisme',
                'description': 'Pneus tourisme - Pour voitures de tourisme'
            },
            {
                'name': '4x4',
                'slug': '4x4',
                'description': 'Pneus 4x4 - Pour véhicules tout-terrain et SUV'
            },
            {
                'name': 'agricole',
                'slug': 'agricole',
                'description': 'Pneus agricole - Pour tracteurs et engins agricoles'
            },
            {
                'name': 'utilitaire',
                'slug': 'utilitaire',
                'description': 'Pneus utilitaire - Pour camionnettes et véhicules commerciaux'
            },
            {
                'name': 'moto',
                'slug': 'moto',
                'description': 'Pneus moto - Pour motos et scooters'
            }
        ]

        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Total categories in database: {Category.objects.count()}')
        )
