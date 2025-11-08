from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Nombre de produits'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'brand', 'size', 'category', 'price', 'old_price', 
        'discount_display', 'stock', 'season', 'is_featured', 'is_active'
    )
    list_filter = (
        'category', 'brand', 'season', 'is_featured', 'is_active', 
        'created_at', 'updated_at'
    )
    search_fields = ('name', 'brand', 'description', 'size')
    prepopulated_fields = {'slug': ('name', 'brand', 'size')}
    readonly_fields = ('created_at', 'updated_at', 'discount_percentage')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'slug', 'description', 'category', 'image')
        }),
        ('Détails produit', {
            'fields': ('brand', 'size', 'season')
        }),
        ('Prix et stock', {
            'fields': ('price', 'old_price', 'stock')
        }),
        ('Options', {
            'fields': ('is_featured', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'discount_percentage'),
            'classes': ('collapse',)
        })
    )

    def discount_display(self, obj):
        if obj.is_on_sale:
            return format_html(
                '<span style="color: red; font-weight: bold;">-{}%</span>',
                obj.discount_percentage
            )
        return '-'
    discount_display.short_description = 'Remise'

    def save_model(self, request, obj, form, change):
        # Auto-generate slug if not provided
        if not obj.slug:
            from django.utils.text import slugify
            obj.slug = slugify(f"{obj.brand}-{obj.name}-{obj.size}")
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('product', 'quantity', 'price', 'total_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user_email', 'status', 'total_amount', 
        'total_items', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('order_number', 'user__email', 'user__username', 'shipping_address')
    readonly_fields = ('order_number', 'total_items', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations commande', {
            'fields': ('order_number', 'user', 'status', 'total_amount')
        }),
        ('Livraison', {
            'fields': ('shipping_address', 'notes')
        }),
        ('Métadonnées', {
            'fields': ('total_items', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email client'
    user_email.admin_order_field = 'user__email'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'product_name', 'quantity', 'price', 'total_price', 'created_at')
    list_filter = ('created_at', 'order__status', 'product__category', 'product__brand')
    search_fields = ('order__order_number', 'product__name', 'product__brand')
    readonly_fields = ('total_price',)
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Numéro de commande'
    order_number.admin_order_field = 'order__order_number'
    
    def product_name(self, obj):
        return f"{obj.product.brand} {obj.product.name}"
    product_name.short_description = 'Produit'
    product_name.admin_order_field = 'product__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'product')
