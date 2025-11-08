from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
import csv
import os
from django.http import HttpResponse, Http404
from django.conf import settings
from django.core.management import call_command
from io import StringIO
from orders.models import Order as o, OrderItem as oi
from .models import Product, Category, StockMovement, OrderItem, Order
from .admin_serializers import AdminProductSerializer, AdminCategorySerializer, AdminProductCreateUpdateSerializer, StockMovementSerializer
from accounts.models import CustomUser
from .permissions import IsAdminOrPurchasing
class AdminProductListCreateView(generics.ListCreateAPIView):
    """Admin view for listing and creating products"""
    queryset = Product.objects.all().select_related('category')
    permission_classes = [IsAdminOrPurchasing]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'brand', 'season', 'is_featured', 'is_active']
    search_fields = ['name', 'brand', 'description', 'size']
    ordering_fields = ['price', 'created_at', 'name', 'stock']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminProductCreateUpdateSerializer
        return AdminProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Custom filters for admin
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        low_stock = self.request.query_params.get('low_stock')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if low_stock == 'true':
            queryset = queryset.filter(stock__lt=10)  # Low stock threshold
            
        return queryset

class AdminProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin view for retrieving, updating, and deleting a specific product"""
    queryset = Product.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminProductCreateUpdateSerializer
        return AdminProductSerializer

class AdminCategoryListCreateView(generics.ListCreateAPIView):
    """Admin view for listing and creating categories"""
    queryset = Category.objects.annotate(product_count=Count('products'))
    serializer_class = AdminCategorySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']

class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin view for retrieving, updating, and deleting a specific category"""
    queryset = Category.objects.all()
    serializer_class = AdminCategorySerializer
    permission_classes = [IsAdminUser]

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard_stats(request):
    """Get dashboard statistics for admin"""
    
    # Basic counts
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    total_categories = Category.objects.count()
    # total_customers = CustomUser.objects.filter(is_staff=False).count()
    total_customers = CustomUser.objects.filter(
    is_staff=False,
    is_superuser=False
).exclude(
    role__in=["sales", "purchasing"]
).count()

    # Order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    # Revenue statistics
    total_revenue = Order.objects.filter(status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Recent orders (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    recent_revenue = Order.objects.filter(
        created_at__gte=thirty_days_ago, 
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Low stock products (less than 10 items)
    low_stock_products = Product.objects.filter(stock__lt=10, is_active=True).count()
    
    # Featured products
    featured_products = Product.objects.filter(is_featured=True, is_active=True).count()
    
    # Products by category
    products_by_category = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).values('name', 'product_count')
    
    # Top selling products (by quantity in completed orders)
    top_selling_products = OrderItem.objects.filter(
        order__status='delivered'
    ).values(
        'product__id', 'product__name', 'product__brand'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    # Recent orders details
    recent_orders_details = Order.objects.filter(
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')[:5].values(
        'id', 'order_number', 'user__email', 'status', 'total_amount', 'created_at'
    )
    
    # Top stock products
    top_stock_products = Product.objects.filter(is_active=True).order_by('-stock')[:5].values(
        'id', 'name', 'brand', 'stock', 'price'
    )
    
    # Low stock products details
    low_stock_details = Product.objects.filter(
        stock__lt=10, is_active=True
    ).order_by('stock')[:5].values(
        'id', 'name', 'brand', 'stock', 'price'
    )
    
    # Price statistics
    price_stats = Product.objects.filter(is_active=True).aggregate(
        avg_price=Avg('price'),
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Recent products (last 30 days)
    recent_products = Product.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # Orders by status
    orders_by_status = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    return Response({
        'total_products': total_products,
        'active_products': active_products,
        'total_categories': total_categories,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': float(total_revenue),
        'recent_orders': recent_orders,
        'recent_revenue': float(recent_revenue),
        'low_stock_products': low_stock_products,
        'featured_products': featured_products,
        'recent_products': recent_products,
        'products_by_category': list(products_by_category),
        'top_selling_products': list(top_selling_products),
        'recent_orders_details': list(recent_orders_details),
        'top_stock_products': list(top_stock_products),
        'low_stock_details': list(low_stock_details),
        'price_stats': price_stats,
        'orders_by_status': list(orders_by_status),
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_update_products(request):
    """Bulk update products (e.g., prices, stock, status)"""
    product_ids = request.data.get('product_ids', [])
    updates = request.data.get('updates', {})
    
    if not product_ids or not updates:
        return Response(
            {'error': 'product_ids et updates sont requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        products = Product.objects.filter(id__in=product_ids)
        count = products.update(**updates)
        
        return Response({
            'message': f'{count} produits mis à jour avec succès',
            'updated_count': count
        })
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la mise à jour: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    

@api_view(['GET'])
@permission_classes([IsAdminUser])
def reports_data(request):
    """Get comprehensive reports data for the reports page"""
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    
    # Get current date and calculate periods
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())
    start_of_day = today


    included_statuses = ['completed', 'delivered', 'processing', 'shipped']

    # Sales statistics
    total_revenue = o.objects.filter(status__in=included_statuses).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # Monthly stats
    monthly_orders = o.objects.filter(
        created_at__date__gte=start_of_month    ,
        status__in=included_statuses
    ).aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount')
    )

    # Weekly stats
    weekly_orders = o.objects.filter(
        created_at__date__gte=start_of_week,
        status__in=included_statuses
    ).aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount')
    )

    # Daily stats
    daily_orders = o.objects.filter(
        created_at__date=start_of_day,
        status__in=included_statuses
    ).aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount')
    )

    # Client and product stats
    total_customers = CustomUser.objects.filter(is_staff=False).count()
    total_products_sold = OrderItem.objects.filter(
        order__status__in=included_statuses
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # Debug: Print some stats
    print(f"Total customers: {total_customers}")
    print(f"Total products sold: {total_products_sold}")
    print(f"Daily orders: {daily_orders}")
    print(f"Monthly orders: {monthly_orders}")

    # Monthly sales evolution (last 6 months)
    monthly_evolution = []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

        month_orders = o.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end,
            status__in=included_statuses
        ).aggregate(
            total_revenue=Sum('total_amount'),  # Use total_amount from Order model
            total_orders=Count('id')
        )

        monthly_evolution.append({
            'mois': month_date.strftime('%b'),
            'ventes': float(month_orders.get('total_revenue', 0) or 0),
            'commandes': month_orders.get('total_orders', 0) or 0
        })

    # Top products by revenue
    top_products = oi.objects.filter(
    order__status__in=included_statuses
    ).values(
        'product_name'  # Direct field from OrderItem
    ).annotate(
        quantity=Sum('quantity'),
        total_revenue=Sum('unit_price')  # Changed from 'price' to 'unit_price'
    ).order_by('-total_revenue')[:5]

    # Top clients by total spent
    top_clients = o.objects.filter(
        status__in=included_statuses
    ).values(
        'user__username', 'user__first_name', 'user__last_name'
    ).annotate(
        total_orders=Count('id'),
        total_spent=Sum('total_amount')  # Use total_amount from Order model
    ).order_by('-total_spent')[:5]

    # Format the response
    reports_data = {
        'stats_ventes': {
            'ventes_jour': float(daily_orders.get('total_revenue', 0) or 0),
            'ventes_hebdo': float(weekly_orders.get('total_revenue', 0) or 0),
            'ventes_mensuel': float(monthly_orders.get('total_revenue', 0) or 0),
            'commandes_jour': daily_orders.get('total_orders', 0) or 0,
            'commandes_hebdo': weekly_orders.get('total_orders', 0) or 0,
            'commandes_mensuel': monthly_orders.get('total_orders', 0) or 0,
            'clients_actifs': total_customers,
            'produits_vendus': total_products_sold
        },
        'ventes_par_mois': monthly_evolution,
        'top_produits': [
        {
            'nom': product['product_name'],  # Changed from f-string with brand
            'ventes': product['quantity'],
            'chiffre': float(product['total_revenue'])
        } for product in top_products
            ],
        'top_clients': [
            {
                'nom': f"{client['user__first_name']} {client['user__last_name']}" if client['user__first_name'] and client['user__last_name'] else client['user__username'],
                'commandes': client['total_orders'],
                'total': float(client['total_spent'])
            } for client in top_clients
        ]
    }

    return Response(reports_data)
@permission_classes([IsAdminUser])
def debug_database_stats(request):
    """Debug endpoint to check database content"""
    from django.db.models import Sum, Count

    # Get basic counts
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='completed').count()
    total_order_items = OrderItem.objects.count()
    total_users = CustomUser.objects.count()
    total_products = Product.objects.count()

    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5].values(
        'id', 'order_number', 'status', 'total_amount', 'created_at', 'user__username'
    )

    # Get recent order items
    recent_items = OrderItem.objects.all().order_by('-created_at')[:5].values(
        'id', 'quantity', 'price', 'product__name', 'order__order_number'
    )

    debug_data = {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_order_items': total_order_items,
        'total_users': total_users,
        'total_products': total_products,
        'recent_orders': list(recent_orders),
        'recent_items': list(recent_items),
    }

    return Response(debug_data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_database_backup(request):
    """Create a database backup and return it as a downloadable file"""
    try:
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'
        filepath = os.path.join(backup_dir, filename)

        # Create the backup using Django's dumpdata command
        with open(filepath, 'w', encoding='utf-8') as backup_file:
            call_command('dumpdata', '--natural-foreign', '--natural-primary', '--indent=2', stdout=backup_file)

        # Read the file and return as response
        with open(filepath, 'r', encoding='utf-8') as backup_file:
            file_data = backup_file.read()

        # Clean up the file
        os.remove(filepath)

        # Return the backup as downloadable response
        response = HttpResponse(file_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la création de la sauvegarde: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_customer_data(request):
    """Export customer data as CSV file"""
    try:
        # Get all customers (non-staff users)
        customers = CustomUser.objects.filter(is_staff=False).values(
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'date_joined', 'last_login', 'is_active'
        )

        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Username', 'Email', 'Prénom', 'Nom', 'Téléphone',
            'Date d\'inscription', 'Dernière connexion', 'Actif'
        ])

        # Write customer data
        for customer in customers:
            writer.writerow([
                customer['id'],
                customer['username'],
                customer['email'],
                customer['first_name'],
                customer['last_name'],
                customer['phone'] or '',
                customer['date_joined'].strftime('%Y-%m-%d %H:%M:%S') if customer['date_joined'] else '',
                customer['last_login'].strftime('%Y-%m-%d %H:%M:%S') if customer['last_login'] else '',
                'Oui' if customer['is_active'] else 'Non'
            ])

        # Get CSV content
        csv_content = output.getvalue()
        output.close()

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'customers_export_{timestamp}.csv'

        # Return CSV as downloadable response
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('\ufeff')  # BOM for Excel compatibility

        return response

    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'export: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class StockMovementListCreateView(generics.ListCreateAPIView):
    queryset = StockMovement.objects.all().select_related('product')
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]