from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "email", "phone", "status", "rating", "orders_count")
    search_fields = ("name", "contact_person", "email")
    list_filter = ("status", "rating")
