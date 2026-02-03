from rest_framework import serializers
from .models import PurchaseOrder, PurchaseOrderItem
from suppliers.models import Supplier
from products.models import Product


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for purchase order items"""
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product', 'reference', 'designation', 
            'unit_price_ht', 'quantity', 'discount', 'total_ht',
            'received_quantity', 'created_at'
        ]
        read_only_fields = ['id', 'total_ht', 'created_at']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for purchase orders"""
    items = PurchaseOrderItemSerializer(many=True, required=False)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'invoice_number', 'supplier', 'supplier_name',
            'note', 'week', 'year', 'subtotal', 'global_discount', 'total',
            'status', 'created_by', 'created_by_name', 'order_date', 
            'confirmed_date', 'received_date', 'updated_at', 'items'
        ]
        read_only_fields = ['id', 'order_number', 'order_date', 'updated_at', 'created_by']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        
        # Create items
        for item_data in items_data:
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                **item_data
            )
        
        # Recalculate totals
        purchase_order.save()
        
        return purchase_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update purchase order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()
            
            # Create new items
            for item_data in items_data:
                PurchaseOrderItem.objects.create(
                    purchase_order=instance,
                    **item_data
                )
        
        return instance


class PurchaseOrderCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for creating purchase orders from frontend
    Matches the structure sent by the frontend
    """
    supplier = serializers.IntegerField()
    date_commande = serializers.DateField(required=False)
    date_livraison_prevue = serializers.DateField(required=False)
    total_ht = serializers.DecimalField(max_digits=10, decimal_places=3, required=False)
    total_ttc = serializers.DecimalField(max_digits=10, decimal_places=3, required=False)
    note = serializers.CharField(required=False, allow_blank=True)
    invoice_number = serializers.CharField(required=False, allow_blank=True)
    week = serializers.CharField(required=False, allow_blank=True)
    year = serializers.CharField(required=False, allow_blank=True)
    global_discount = serializers.DecimalField(max_digits=5, decimal_places=2, default=0, required=False)
    articles = serializers.ListField(child=serializers.DictField())
    
    def create(self, validated_data):
        items_data = validated_data.pop('articles', [])
        
        # Get supplier
        supplier_id = validated_data.pop('supplier')
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Extract and remove fields not in PurchaseOrder model
        validated_data.pop('date_commande', None)
        validated_data.pop('date_livraison_prevue', None)
        validated_data.pop('total_ht', None)
        validated_data.pop('total_ttc', None)
        
        # Set created_by from request user
        request = self.context.get('request')
        created_by = None
        if request and hasattr(request, 'user'):
            created_by = request.user
        
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            supplier=supplier,
            created_by=created_by,
            status='confirmed',
            **validated_data
        )
        
        # Create items and UPDATE STOCK (we're buying from supplier - ADD to stock)
        total_amount = 0  # Track total for the purchase order
        
        for item_data in items_data:
            # Prefer id (PK) first (frontend sends productId), then reference
            product = None
            try:
                raw_id = item_data.get('id')
                if raw_id is not None:
                    pid = int(raw_id) if not isinstance(raw_id, int) else raw_id
                    product = Product.objects.filter(id=pid).first()
                if not product and item_data.get('reference'):
                    product = Product.objects.filter(
                        reference=str(item_data['reference']).strip()
                    ).first()
            except (ValueError, TypeError):
                pass
            if not product:
                ref = item_data.get('reference') or item_data.get('id') or '?'
                raise serializers.ValidationError(
                    {'articles': f'Produit non trouvé pour la référence: {ref}. Vérifiez la référence ou l\'ID.'}
                )

            quantity = int(item_data.get('quantite', item_data.get('quantity', 1)))
            unit_price = float(item_data.get('prix_unitaire', item_data.get('priceHT', 0)))
            discount = float(item_data.get('discount', 0))
            item_total = float(item_data.get('total_ht', item_data.get('totalHT', 0)))
            
            # If item_total is not provided, calculate it
            if item_total == 0:
                base_total = unit_price * quantity
                item_total = base_total - (base_total * discount / 100)
            
            # Add to purchase order total
            total_amount += item_total
            
            # Create the purchase order item
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product=product,
                reference=item_data.get('reference', ''),
                designation=item_data.get('nom', item_data.get('designation', '')),
                unit_price_ht=unit_price,
                quantity=quantity,
                discount=discount,
                total_ht=item_total,
                received_quantity=quantity  # Mark as received immediately
            )
            
            # CRITICAL: INCREASE stock (we're buying from supplier)
            if product:
                product.stock += quantity  # ADD to existing stock
                product.save()
                print(f"✅ Stock updated: {product.reference} - Added {quantity} units. New stock: {product.stock}")
        
        # Apply global discount if any
        global_discount = float(validated_data.get('global_discount', 0))
        if global_discount > 0:
            total_amount = total_amount - (total_amount * global_discount / 100)
        
        # Update the purchase order total
        purchase_order.total = total_amount
        purchase_order.subtotal = total_amount
        purchase_order.save()
        
        # Update supplier orders count
        supplier.orders_count += 1
        supplier.save()
        
        return purchase_order
