from django.core.management.base import BaseCommand
from orders.models import Delivery

class Command(BaseCommand):
    help = 'Update delivery client names to show actual client names instead of Purchase Order identifiers'

    def handle(self, *args, **kwargs):
        deliveries = Delivery.objects.all()  # Update all deliveries
        
        updated_count = 0
        for delivery in deliveries:
            old_client = delivery.client
            client_name = None
            
            # Try to get client name from order's shipping address
            if delivery.order:
                shipping_address = delivery.order.shipping_address
                if shipping_address:
                    first_name = shipping_address.get('first_name', '')
                    last_name = shipping_address.get('last_name', '')
                    client_name = f"{first_name} {last_name}".strip()
                
                # Fallback to user if shipping address doesn't have name
                if not client_name and delivery.order.user:
                    first_name = delivery.order.user.first_name or ""
                    last_name = delivery.order.user.last_name or ""
                    client_name = f"{first_name} {last_name}".strip() or delivery.order.user.email
            
            # Fallback: try through purchase order
            elif delivery.purchase_order and delivery.purchase_order.order:
                order = delivery.purchase_order.order
                shipping_address = order.shipping_address
                if shipping_address:
                    first_name = shipping_address.get('first_name', '')
                    last_name = shipping_address.get('last_name', '')
                    client_name = f"{first_name} {last_name}".strip()
                
                # Fallback to user
                if not client_name and order.user:
                    first_name = order.user.first_name or ""
                    last_name = order.user.last_name or ""
                    client_name = f"{first_name} {last_name}".strip() or order.user.email
            
            # Update if we found a name and it's different
            if client_name and client_name != old_client:
                delivery.client = client_name
                delivery.save()
                updated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated Delivery {delivery.id}: "{old_client}" → "{client_name}"'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated {updated_count} deliveries'
            )
        )
