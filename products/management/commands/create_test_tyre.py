"""
Create a test tyre product for Achats/testing.
Run: python manage.py create_test_tyre
Product will appear in DB and on website (boutique, admin produits, achats search).
"""
from django.core.management.base import BaseCommand
from products.models import Product, Category


class Command(BaseCommand):
    help = 'Create one test tyre product for testing (website + database)'

    def handle(self, *args, **options):
        # Ensure category exists
        category, _ = Category.objects.get_or_create(
            slug='tourisme',
            defaults={
                'name': 'tourisme',
                'description': 'Pneus tourisme - Pour voitures de tourisme',
            },
        )

        reference = 'TEST-TYRE-001'
        base_slug = 'continental-pneu-test-205-55-r16'
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        product, created = Product.objects.update_or_create(
            reference=reference,
            defaults={
                'name': 'Pneu Test Continental 205/55 R16',
                'slug': slug,
                'description': 'Pneu de test pour achats et commandes. Continental - toutes saisons.',
                'price': 199.99,
                'old_price': None,
                'category': category,
                'image': '',
                'image_2': None,
                'image_3': None,
                'brand': 'Continental',
                'size': '205/55 R16',
                'season': 'all_season',
                'stock': 10,
                'is_featured': False,
                'is_active': True,
                'designation': 'Pneu test Continental 205/55 R16',
                'type': 'Tourisme',
                'emplacement': 'Rayon A',
                'fabrication_date': None,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Test tyre created: id={product.id} | ref={product.reference} | {product.name}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'🔄 Test tyre updated: id={product.id} | ref={product.reference} | {product.name}'
            ))
        self.stdout.write(
            f'   → Website: /boutique/{product.slug}\n'
            f'   → Admin produits: list + edit\n'
            f'   → Achats: search by ref "{product.reference}" or add from list (id={product.id})'
        )
