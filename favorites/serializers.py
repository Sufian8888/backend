from rest_framework import serializers
from .models import Favorite
from products.serializers import ProductSerializer

class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'product', 'created_at')

class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating favorites"""
    
    class Meta:
        model = Favorite
        fields = ('product',)
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
