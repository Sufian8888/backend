from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('product', 'quantity', 'total_price')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'total_price', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('total_items', 'total_price', 'created_at', 'updated_at')
    inlines = [CartItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart_user', 'product', 'quantity', 'total_price', 'created_at')
    list_filter = ('created_at', 'product__category', 'product__brand')
    search_fields = ('cart__user__email', 'product__name', 'product__brand')
    readonly_fields = ('total_price',)

    def cart_user(self, obj):
        return obj.cart.user.email
    cart_user.short_description = 'Utilisateur'
    cart_user.admin_order_field = 'cart__user__email'
