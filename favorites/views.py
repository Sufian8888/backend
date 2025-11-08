from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from .models import Favorite
from .serializers import FavoriteSerializer
from products.models import Product

class FavoriteListView(generics.ListAPIView):
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('product', 'product__category')

@api_view(['POST'])
def add_to_favorites(request):
    product_id = request.data.get('product_id')
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    try:
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return Response({
                'message': 'Produit ajouté aux favoris',
                'favorite': FavoriteSerializer(favorite).data
            })
        else:
            return Response({
                'message': 'Produit déjà dans les favoris',
                'favorite': FavoriteSerializer(favorite).data
            })
    except IntegrityError:
        return Response({
            'message': 'Produit déjà dans les favoris'
        })

@api_view(['DELETE'])
def remove_from_favorites(request, product_id):
    favorite = get_object_or_404(
        Favorite, 
        user=request.user, 
        product_id=product_id
    )
    favorite.delete()
    
    return Response({'message': 'Produit supprimé des favoris'})

@api_view(['GET'])
def check_favorite(request, product_id):
    is_favorite = Favorite.objects.filter(
        user=request.user,
        product_id=product_id
    ).exists()
    
    return Response({'is_favorite': is_favorite})

@api_view(['DELETE'])
def clear_favorites(request):
    """Clear all favorites for user"""
    count = Favorite.objects.filter(user=request.user).count()
    Favorite.objects.filter(user=request.user).delete()
    
    return Response({
        'message': f'{count} favoris supprimés'
    })

@api_view(['POST'])
def toggle_favorite(request, product_id):
    """Toggle favorite status for a product"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    favorite = Favorite.objects.filter(user=request.user, product=product).first()
    
    if favorite:
        favorite.delete()
        return Response({
            'message': 'Produit supprimé des favoris',
            'is_favorite': False
        })
    else:
        favorite = Favorite.objects.create(user=request.user, product=product)
        return Response({
            'message': 'Produit ajouté aux favoris',
            'is_favorite': True,
            'favorite': FavoriteSerializer(favorite).data
        })
