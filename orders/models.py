from django.db import models
from django.conf import settings

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_orders'
    )
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    shipping_address = models.JSONField()
    billing_address = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Warranty information fields
    warranty_accepted = models.BooleanField(default=False)
    warranty_vehicle_registration = models.CharField(max_length=100, blank=True, null=True)
    warranty_vehicle_mileage = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.order_number} - {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=255)
    product_id = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    specifications = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

class PurchaseOrder(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("confirmé", "Confirmé"),
        ("livré", "Livré"),
    ]

    PRIORITE_CHOICES = [
        ("normale", "Normale"),
        ("urgent", "Urgent"),
    ]
    order = models.ForeignKey(
            "Order",
            on_delete=models.CASCADE,
            related_name="purchase_orders",
            null=True,  # Temporarily allow null for migration
            blank=True
        )
    date_commande = models.DateField()
    date_livraison_prevue = models.DateField()
    total_ht = models.DecimalField(max_digits=10, decimal_places=2)
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_attente")
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default="normale")

    def __str__(self):
        return f"PO-{self.id} - {self.date_commande}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="articles")
    nom = models.CharField(max_length=255)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nom} ({self.quantite})"




class Delivery(models.Model):
    # order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="deliveries")
    purchase_order = models.ForeignKey("PurchaseOrder", on_delete=models.CASCADE, related_name="deliveries", null=True, blank=True)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="deliveries", null=True, blank=True)
    client = models.CharField(max_length=255)
    adresse = models.TextField()
    transporteur = models.CharField(max_length=255)
    statut = models.CharField(max_length=50, choices=[
        ("prepare", "En préparation"),
        ("en_route", "En route"),
        ("livre", "Livré"),
    ], default="prepare")
    date_expedition = models.DateField(null=True, blank=True)
    date_livraison = models.DateField(null=True, blank=True)
    colis = models.IntegerField(default=0)

    def __str__(self):
        if self.purchase_order:
            return f"Delivery {self.id} for PO {self.purchase_order.id}"
        elif self.order:
            return f"Delivery {self.id} for Order {self.order.id}"
        return f"Delivery {self.id}"


