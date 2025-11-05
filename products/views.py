from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from django.core.files.base import ContentFile
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Product, Category, SiteSettings
from .serializers import ProductSerializer,ProductDetailSerializer, CategorySerializer, SiteSettingsSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.db import models

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'brand', 'season', 'is_featured']
    search_fields = ['name', 'brand', 'description', 'size']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        on_sale = self.request.query_params.get('on_sale')

        width = self.request.query_params.get('width')
        height = self.request.query_params.get('height')
        diameter = self.request.query_params.get('diameter')
        speed_rating = self.request.query_params.get('speedRating')
        load_index = self.request.query_params.get('loadIndex')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if on_sale == 'true':
            queryset = queryset.filter(old_price__isnull=False, old_price__gt=0)

        # Filter by size string "205/55R16"
        if width:
            queryset = queryset.filter(size__startswith=width + "/")
        if height:
            queryset = queryset.filter(size__icontains="/" + height)
        if diameter:
            queryset = queryset.filter(size__iendswith=str(diameter))
        if speed_rating:
            queryset = queryset.filter(size__icontains=speed_rating)
        # load_index not stored yet unless you add a field

        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class FeaturedProductsView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True, is_featured=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

@api_view(['GET'])
@permission_classes([AllowAny])
def product_search_suggestions(request):
    """Get search suggestions for products"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response([])
    
    # Get brand suggestions
    brands = Product.objects.filter(
        Q(brand__icontains=query) & Q(is_active=True)
    ).values_list('brand', flat=True).distinct()[:5]
    
    # Get product name suggestions
    products = Product.objects.filter(
        Q(name__icontains=query) & Q(is_active=True)
    ).values_list('name', flat=True).distinct()[:5]
    
    suggestions = list(brands) + list(products)
    return Response(suggestions[:10])

@api_view(['GET'])
@permission_classes([AllowAny])
def product_filters(request):
    """Get available filter options"""
    brands = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct().order_by('brand')
    seasons = Product.objects.filter(is_active=True).values_list('season', flat=True).distinct()
    
    # Price range
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=models.Min('price'),
        max_price=models.Max('price')
    )
    
    return Response({
        'brands': list(brands),
        'seasons': [
            {'value': season, 'label': dict(Product._meta.get_field('season').choices)[season]}
            for season in seasons
        ],
        'price_range': price_range
    })


@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def site_settings(request):
    settings, created = SiteSettings.objects.get_or_create(pk=1)
    
    if request.method == 'GET':
        serializer = SiteSettingsSerializer(settings)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = SiteSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)