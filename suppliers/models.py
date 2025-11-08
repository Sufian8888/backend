from django.db import models

class Supplier(models.Model):
    STATUS_CHOICES = [
        ("active", "Actif"),
        ("inactive", "Inactif"),
    ]

    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    specialties = models.JSONField(default=list, blank=True)  # e.g. ["Pneus été", "Pneus hiver"]
    rating = models.IntegerField(default=0)
    orders_count = models.IntegerField(default=0)
    delivery_time = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return self.name
