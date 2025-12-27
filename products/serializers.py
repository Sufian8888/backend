from rest_framework import serializers
from .models import Product, Category, SiteSettings

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'product_count')

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    season_display = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'price', 'old_price',
            'category', 'image', 'image_2', 'image_3', 'brand', 'size', 'season', 'season_display',
            'stock', 'is_featured', 'is_on_sale', 'discount_percentage',
            'created_at'
        )

    def get_season_display(self, obj):
        return obj.get_season_display()

class ProductDetailSerializer(ProductSerializer):
    """Extended serializer for product detail view"""
    related_products = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ('related_products',)

    def get_related_products(self, obj):
        # Get related products from same category and brand
        related = Product.objects.filter(
            category=obj.category,
            brand=obj.brand,
            is_active=True
        ).exclude(id=obj.id)[:4]
        
        return ProductSerializer(related, many=True, context=self.context).data




class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = '__all__'