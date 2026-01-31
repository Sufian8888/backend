from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'reference', 'designation', 'unit_price_ht', 'quantity', 'discount', 'total_ht', 'received_quantity']
    readonly_fields = ['total_ht']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'invoice_number', 'week', 'year', 'total', 'status', 'order_date', 'created_by']
    list_filter = ['status', 'supplier', 'year', 'order_date']
    search_fields = ['order_number', 'invoice_number', 'supplier__name', 'note']
    readonly_fields = ['order_number', 'order_date', 'confirmed_date', 'received_date', 'updated_at']
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Information Générale', {
            'fields': ('order_number', 'invoice_number', 'supplier', 'created_by', 'status')
        }),
        ('Période', {
            'fields': ('week', 'year')
        }),
        ('Montants', {
            'fields': ('subtotal', 'global_discount', 'total')
        }),
        ('Notes', {
            'fields': ('note',)
        }),
        ('Dates', {
            'fields': ('order_date', 'confirmed_date', 'received_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_received', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for order in queryset:
            if order.status == 'draft':
                order.status = 'confirmed'
                order.confirmed_date = timezone.now()
                order.save()
                updated += 1
        self.message_user(request, f'{updated} commande(s) confirmée(s).')
    mark_as_confirmed.short_description = "Marquer comme confirmé"
    
    def mark_as_received(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for order in queryset:
            if order.status == 'confirmed':
                order.status = 'received'
                order.received_date = timezone.now()
                order.save()
                
                # Update product stock
                for item in order.items.all():
                    if item.product:
                        qty_to_add = item.received_quantity if item.received_quantity > 0 else item.quantity
                        item.product.stock += qty_to_add
                        item.product.save()
                
                updated += 1
        self.message_user(request, f'{updated} commande(s) reçue(s) et stock mis à jour.')
    mark_as_received.short_description = "Marquer comme reçu (+ mise à jour stock)"
    
    def mark_as_cancelled(self, request, queryset):
        updated = 0
        for order in queryset:
            if order.status != 'received':
                order.status = 'cancelled'
                order.save()
                updated += 1
        self.message_user(request, f'{updated} commande(s) annulée(s).')
    mark_as_cancelled.short_description = "Annuler"


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'product', 'reference', 'designation', 'unit_price_ht', 'quantity', 'discount', 'total_ht', 'received_quantity']
    list_filter = ['purchase_order__status', 'purchase_order__supplier']
    search_fields = ['reference', 'designation', 'product__name', 'purchase_order__order_number']
    readonly_fields = ['total_ht', 'created_at']
    
    fieldsets = (
        ('Commande', {
            'fields': ('purchase_order',)
        }),
        ('Produit', {
            'fields': ('product', 'reference', 'designation')
        }),
        ('Prix et Quantité', {
            'fields': ('unit_price_ht', 'quantity', 'discount', 'total_ht')
        }),
        ('Réception', {
            'fields': ('received_quantity',)
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
