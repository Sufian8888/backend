from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="Utilisateur")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produit")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"
