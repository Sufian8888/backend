from rest_framework import serializers
from .models import Delivery, Order, OrderItem, PurchaseOrder, PurchaseOrderItem, CRIBalance
from accounts.serializers import UserSerializer  # import your CustomUser serializer

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'product_id', 'quantity', 'unit_price', 'total_price', 'specifications']
        # Exclude 'order' field - it will be set automatically


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True)
    order_number = serializers.CharField(read_only=True)  # Make read-only to auto-generate
    warranty = serializers.JSONField(required=False, allow_null=True, write_only=True)
    delivery_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)

    class Meta:
        model = Order
        fields = "__all__"

    def create(self, validated_data):
        from django.utils import timezone
        from decimal import Decimal
        
        # Extract nested data
        items_data = validated_data.pop('items')
        warranty_data = validated_data.pop('warranty', None)
        
        # Process warranty data if provided
        if warranty_data:
            validated_data['warranty_accepted'] = warranty_data.get('accepted', False)
            validated_data['warranty_vehicle_registration'] = warranty_data.get('vehicleRegistration', '')
            validated_data['warranty_vehicle_mileage'] = warranty_data.get('vehicleMileage', '')
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Handle CRI balance: if payment method is CRI, update user's loan balance
        if order.payment_method == 'cri' and order.cri_remaining > 0:
            user = order.user
            cri_balance, _ = CRIBalance.objects.get_or_create(user=user)
            cri_balance.balance += Decimal(str(order.cri_remaining))
            cri_balance.save()
        
        # Generate order number with PS + year + sequential format
        if not order.order_number:
            year = timezone.now().strftime('%y')  # Get 2-digit year
            prefix = f'PS{year}'
            # Find the highest existing order number for this year
            last_order = Order.objects.filter(
                order_number__startswith=prefix
            ).order_by('-order_number').first()
            if last_order and last_order.order_number.startswith(prefix):
                last_seq = int(last_order.order_number[len(prefix):])
            else:
                last_seq = 0
            order.order_number = f'{prefix}{last_seq + 1:06d}'
            order.save()
        
        # Create order items
        for item in items_data:
            OrderItem.objects.create(order=order, **item)
        
        return order




class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PurchaseOrderItem
        fields = ["id", "nom", "quantite", "prix_unitaire"]

# class PurchaseOrderSerializer(serializers.ModelSerializer):
#     articles = PurchaseOrderItemSerializer(many=True)

#     class Meta:
#         model = PurchaseOrder
#         fields = ["id", "fournisseur", "date_commande", "date_livraison_prevue", "total_ht", "total_ttc", "statut", "priorite", "articles"]

#     def create(self, validated_data):
#         articles_data = validated_data.pop('articles', [])
#         purchase_order = PurchaseOrder.objects.create(**validated_data)

#         for article_data in articles_data:
#             PurchaseOrderItem.objects.create(
#                 purchase_order=purchase_order,
#                 **article_data
#             )
#         return purchase_order
class PurchaseOrderSerializer(serializers.ModelSerializer):
    articles = PurchaseOrderItemSerializer(many=True)
    # Make order field optional and handle validation manually
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), 
        required=False, 
        allow_null=True
    )
    order_id = serializers.IntegerField(source="order.id", read_only=True, allow_null=True)

    class Meta:
        model = PurchaseOrder
        fields = ["id","order_id","order", "date_commande", "date_livraison_prevue", "total_ht", "total_ttc", "statut", "priorite", "articles"]
    
    def validate_order(self, value):
        """Custom validation for order field"""
        if value is None:
            return None
        # If value is provided, it's already validated by PrimaryKeyRelatedField
        return value

    def create(self, validated_data):
        articles_data = validated_data.pop("articles", [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        for article_data in articles_data:
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                nom=article_data.get("nom"),
                quantite=article_data.get("quantite"),
                prix_unitaire=article_data.get("prix_unitaire")
            )
        return purchase_order
    def update(self, instance, validated_data):
        # Update basic fields
        instance.order = validated_data.get("order", instance.order)

        instance.statut = validated_data.get("statut", instance.statut)
        instance.priorite = validated_data.get("priorite", instance.priorite)
        instance.date_commande = validated_data.get("date_commande", instance.date_commande)
        instance.date_livraison_prevue = validated_data.get("date_livraison_prevue", instance.date_livraison_prevue)
        instance.total_ht = validated_data.get("total_ht", instance.total_ht)
        instance.total_ttc = validated_data.get("total_ttc", instance.total_ttc)
        instance.save()

        # Update articles if provided
        articles_data = validated_data.get("articles")
        if articles_data is not None:
            instance.articles.all().delete()
            for article_data in articles_data:
                PurchaseOrderItem.objects.create(
                    purchase_order=instance,
                    nom=article_data.get("nom"),
                    quantite=article_data.get("quantite"),
                    prix_unitaire=article_data.get("prix_unitaire")
                )
        
        # Create delivery when purchase order is confirmed
        print(f"DEBUG: PO {instance.id} - Status: {instance.statut}, Order: {instance.order}")
        
        # if instance.statut == "confirmé":
        #     if instance.order:
        #         # Check if delivery already exists for this specific purchase order
        #         delivery_identifier = f"PO-{instance.id}"
                
        #         existing_delivery = Delivery.objects.filter(
        #             order=instance.order,
        #             client__contains=delivery_identifier
        #         ).first()
                
        #         print(f"DEBUG: PO {instance.id} - Existing delivery: {existing_delivery}")
                
        #         if not existing_delivery:
        #             try:
        #                 new_delivery = Delivery.objects.create(
        #                     order=instance.order,
        #                     client=f"{instance.fournisseur} ({delivery_identifier})",
        #                     adresse="Adresse à définir",
        #                     transporteur="Transporteur à assigner",
        #                     statut="prepare",
        #                     colis=sum(item.quantite for item in instance.articles.all())
        #                 )
        #                 print(f"SUCCESS: Created delivery {new_delivery.id} for PO {instance.id}")
        #             except Exception as e:
        #                 print(f"ERROR: Failed to create delivery for PO {instance.id}: {e}")
        #         else:
        #             print(f"SKIP: Delivery already exists for PO {instance.id}")
        #     else:
        #         print(f"ERROR: PO {instance.id} has no associated order - cannot create delivery")
        # else:
        #     print(f"SKIP: PO {instance.id} status is '{instance.statut}', not 'confirmé'")

        if instance.statut == "confirmé":
            # Check if delivery already exists for this purchase order
            delivery_identifier = f"PO-{instance.id}"
            
            existing_delivery = Delivery.objects.filter(
                purchase_order=instance,
                client__contains=delivery_identifier
            ).first()
            
            print(f"DEBUG: PO {instance.id} - Existing delivery: {existing_delivery}")
            
            if not existing_delivery:
                try:
                    # Get client name from the order's shipping address
                    client_name = "Client inconnu"
                    if instance.order:
                        shipping_address = instance.order.shipping_address
                        if shipping_address:
                            first_name = shipping_address.get('first_name', '')
                            last_name = shipping_address.get('last_name', '')
                            client_name = f"{first_name} {last_name}".strip()
                        
                        # Fallback to user name if shipping address doesn't have name
                        if not client_name or client_name == "":
                            if instance.order.user:
                                first_name = instance.order.user.first_name or ""
                                last_name = instance.order.user.last_name or ""
                                client_name = f"{first_name} {last_name}".strip() or instance.order.user.email
                    
                    new_delivery = Delivery.objects.create(
                        purchase_order=instance,
                        order=instance.order,  # This can be null
                        client=client_name,
                        adresse="Entrepôt principal",  # Your warehouse address
                        transporteur="À assigner",
                        statut="prepare",
                        colis=sum(item.quantite for item in instance.articles.all())
                    )
                    print(f"SUCCESS: Created delivery {new_delivery.id} for PO {instance.id} - Client: {client_name}")
                except Exception as e:
                    print(f"ERROR: Failed to create delivery for PO {instance.id}: {e}")
            else:
                print(f"SKIP: Delivery already exists for PO {instance.id}")

        return instance

class DeliverySerializer(serializers.ModelSerializer):
    commande = serializers.SerializerMethodField()
    
    def get_commande(self, obj):
        if obj.purchase_order:
            return f"PO-{obj.purchase_order.id}"
        elif obj.order:
            return str(obj.order.id)
        return "N/A"
    dateExpedition = serializers.DateField(source="date_expedition", allow_null=True)
    dateLivraison = serializers.DateField(source="date_livraison", allow_null=True)

    class Meta:
        model = Delivery
        fields = [
            "id", "commande", "client", "adresse", "transporteur",
            "statut", "dateExpedition", "dateLivraison", "colis"
        ]