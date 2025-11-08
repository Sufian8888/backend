from rest_framework import serializers
from .models import Product, Category, StockMovement

class AdminCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_product_count(self, obj):
        return obj.products.count()

class AdminProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    season_display = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_season_display(self, obj):
        return obj.get_season_display()

class AdminProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    
    class Meta:
        model = Product
        fields = '__all__'

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être positif")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif")
        return value

    def validate(self, data):
        # Validate old_price is greater than price if provided
        if data.get('old_price') and data.get('price'):
            if data['old_price'] <= data['price']:
                raise serializers.ValidationError({
                    'old_price': 'L\'ancien prix doit être supérieur au prix actuel'
                })
        return data
    
class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'