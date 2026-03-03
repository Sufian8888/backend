import re
from django.core.management.base import BaseCommand
from products.models import Product


def detect_brand(name: str) -> str | None:
    """Extract brand dynamically from product name.
    Pattern: PNEU [BRAND] [size...]
    e.g. 'PNEU AMINE 175/70R14' → 'Amine'
         'PNEU CONTINENTAL 205/55R16' → 'Continental'
         'PNEU LAUFENN 215/60R16C' → 'Laufenn'
    """
    name_clean = re.sub(r'^(PNEU|TIRE|TYRE)\s+', '', name.strip(), flags=re.IGNORECASE)
    parts = name_clean.split()
    if parts and re.match(r'^[A-Za-z]+$', parts[0]):
        return parts[0].capitalize()
    return None


class Command(BaseCommand):
    help = 'Fix products that have wrong/default brand (Continental) by re-detecting from name'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without saving',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        # Target products where brand looks wrong:
        # 1. Brand is "Continental" but name doesn't contain "CONTINENTAL"
        # 2. Brand is empty/null
        products = Product.objects.filter(brand__iexact='continental') | Product.objects.filter(brand='')

        for product in products:
            detected = detect_brand(product.name)
            if not detected:
                skipped += 1
                continue

            # Only fix if the current brand doesn't match what's in the name
            if product.brand.upper() != detected.upper():
                self.stdout.write(
                    f"  [{product.id}] {product.name[:60]}\n"
                    f"       brand: '{product.brand}' → '{detected}'"
                )
                if not dry_run:
                    product.brand = detected
                    product.save(update_fields=['brand'])
                updated += 1
            else:
                skipped += 1

        mode = '(DRY RUN) ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f"\n{mode}Done. Updated: {updated}, Skipped (already correct): {skipped}"
        ))
