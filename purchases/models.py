from django.db import models
from django.contrib.auth import get_user_model
from suppliers.models import Supplier
from products.models import Product

User = get_user_model()


class PurchaseOrder(models.Model):
    """
    COMPANY PURCHASE ORDER - Buying FROM Suppliers
    
    CRITICAL DIFFERENCE:
    - orders.Order: Company SELLS TO clients → stock DECREASES
    - purchases.PurchaseOrder: Company BUYS FROM suppliers → stock INCREASES
    
    When company buys 3 tires from supplier:
    1. PurchaseOrder created with supplier info
    2. PurchaseOrderItem created for each product (quantity=3)
    3. When confirmed/received: product.stock += 3 (ADDS to inventory)
    4. These products now available to sell to clients
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('received', 'Reçue'),
        ('cancelled', 'Annulée'),
    ]

    # Order identification
    order_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro de commande")
    invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Numéro de facture")
    
    # Supplier information
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT, 
        related_name='purchase_orders',
        verbose_name="Fournisseur"
    )
    
    # Order details
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    week = models.CharField(max_length=2, blank=True, null=True, verbose_name="Semaine")
    year = models.CharField(max_length=4, blank=True, null=True, verbose_name="Année")
    
    # Financial information
    subtotal = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Sous-total")
    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Remise globale (%)")
    total = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Total HT")
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Statut")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_purchases', verbose_name="Créé par")
    
    # Dates
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de commande")
    confirmed_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de confirmation")
    received_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de réception")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Bon de Commande Fournisseur"
        verbose_name_plural = "Bons de Commande Fournisseurs"
        ordering = ['-order_date']

    def __str__(self):
        return f"Achat #{self.order_number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        # Auto-generate order number if not set
        if not self.order_number:
            from django.utils import timezone
            now = timezone.now()
            count = PurchaseOrder.objects.filter(
                order_date__year=now.year,
                order_date__month=now.month
            ).count() + 1
            self.order_number = f"ACH-{now.year}{now.month:02d}-{count:04d}"
        
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    """
    Individual items in a purchase order
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Bon de commande"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name='purchase_items',
        verbose_name="Produit"
    )
    
    # Item details
    reference = models.CharField(max_length=100, verbose_name="Référence")
    designation = models.CharField(max_length=255, verbose_name="Désignation")
    
    # Pricing
    unit_price_ht = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Prix unitaire HT")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Remise (%)")
    total_ht = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Total HT")
    
    # Tracking
    received_quantity = models.PositiveIntegerField(default=0, verbose_name="Quantité reçue")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

    def __str__(self):
        return f"{self.reference} - {self.designation} (x{self.quantity})"

    def save(self, *args, **kwargs):
        # Auto-calculate total
        base_total = self.unit_price_ht * self.quantity
        self.total_ht = base_total - (base_total * self.discount / 100)
        super().save(*args, **kwargs)
