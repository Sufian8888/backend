from django.contrib import admin
from django.utils.html import format_html
from .models import Favorite

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_info', 'product_price', 'created_at')
    list_filter = ('created_at', 'product__category', 'product__brand', 'product__season')
    search_fields = ('user__email', 'user__username', 'product__name', 'product__brand')
    readonly_fields = ('created_at',)
    
    def product_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{} - {}</small>',
            obj.product.name,
            obj.product.brand,
            obj.product.size
        )
    product_info.short_description = 'Produit'
    
    def product_price(self, obj):
        if obj.product.is_on_sale:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} €</span><br>'
                '<small style="text-decoration: line-through;">{} €</small>',
                obj.product.price,
                obj.product.old_price
            )
        return f"{obj.product.price} €"
    product_price.short_description = 'Prix'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')
