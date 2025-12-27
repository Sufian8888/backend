from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Ancien prix")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Catégorie")
    image = models.URLField(max_length=1000, blank=True, verbose_name="Image principale")
    image_2 = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Image 2")
    image_3 = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Image 3")
    brand = models.CharField(max_length=100, verbose_name="Marque")
    size = models.CharField(max_length=100, verbose_name="Taille")  # Increased from 50 to 100
    season = models.CharField(max_length=20, choices=[
        ('summer', 'Été'),
        ('winter', 'Hiver'),
        ('all_season', 'Toutes saisons')
    ], verbose_name="Saison")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    # Manual entry fields
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="Référence")
    designation = models.CharField(max_length=255, blank=True, null=True, verbose_name="Désignation")
    type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Type")
    emplacement = models.CharField(max_length=255, blank=True, null=True, verbose_name="Emplacement")
    fabrication_date = models.DateField(blank=True, null=True, verbose_name="Date de fabrication")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return f"{self.brand} {self.name} - {self.size}"

    @property
    def is_on_sale(self):
        return self.old_price and self.old_price > self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Utilisateur")
    order_number = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Numéro de commande")
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending', verbose_name="Statut")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total")
    shipping_address = models.TextField(verbose_name="Adresse de livraison")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
    
    def save(self, *args, **kwargs):
        if not self.order_number and not self.pk:
            # For new orders, save first to get pk, then generate order number
            super().save(*args, **kwargs)
            from django.utils import timezone
            year = timezone.now().strftime('%y')  # Get 2-digit year
            # Get the count of orders created this year
            year_start = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            order_count = Order.objects.filter(created_at__gte=year_start).count()
            self.order_number = f'PS{year}{order_count:06d}'
            # Use update to avoid recursion
            Order.objects.filter(pk=self.pk).update(order_number=self.order_number)
        elif not self.order_number and self.pk:
            # Already has pk but no order number
            from django.utils import timezone
            year = timezone.now().strftime('%y')
            year_start = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            order_count = Order.objects.filter(created_at__gte=year_start).count()
            self.order_number = f'PS{year}{order_count:06d}'
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Commande {self.order_number} - {self.user.email}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produit")
    quantity = models.PositiveIntegerField(verbose_name="Quantité")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")  # Price at time of order
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} - Commande {self.order.order_number}"
    
    @property
    def total_price(self):
        return self.quantity * self.price


### Adding Movement Stock Model ###
class StockMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('in', 'Entrée'),          # Stock added
        ('out', 'Sortie'),         # Stock removed (sale or adjustment)
        ('adjustment', 'Ajustement')  # Manual adjustment
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    product_name = models.CharField(max_length=200, blank=True)  # Store product name at time of movement
    type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)  # optional
    reference = models.CharField(max_length=100, blank=True)  # e.g., order number or invoice
    created_by = models.CharField(max_length=100, blank=True)  # optional user/admin
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"

    def __str__(self):
        return f"{self.get_type_display()} {self.quantity} x {self.product.name}"


class SiteSettings(models.Model):
    # Boutique settings
    nom_boutique = models.CharField(max_length=255, default="PneuShop Tunisia")
    description = models.TextField(default="Votre spécialiste en pneumatiques")
    adresse = models.TextField(default="Avenue Habib Bourguiba, Tunis")
    telephone = models.CharField(max_length=20, default="+216 71 123 456")
    email = models.EmailField(default="contact@pneushop.tn")
    horaires = models.CharField(max_length=255, default="Lun-Sam: 8h-18h")
    
    # Notifications
    email_commandes = models.BooleanField(default=True)
    email_stock = models.BooleanField(default=True)
    sms_clients = models.BooleanField(default=False)
    push_admin = models.BooleanField(default=True)
    
    # Security
    session_timeout = models.IntegerField(default=30)
    mot_de_passe_force = models.BooleanField(default=True)
    authentification_double = models.BooleanField(default=False)
    journalisation = models.BooleanField(default=True)
    
    # System
    maintenance_mode = models.BooleanField(default=False)
    sauvegarde_auto = models.BooleanField(default=True)
    langue_principale = models.CharField(max_length=10, default="fr")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"