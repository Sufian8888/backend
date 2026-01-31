# Purchase Orders (Achats) - Backend Implementation

## Overview
Complete backend structure for managing purchase orders from suppliers (buying inventory).

## Created Files

### 1. Models (`purchases/models.py`)
- **PurchaseOrder**: Main purchase order model
  - `order_number`: Auto-generated format ACH-YYYYMM-XXXX
  - `supplier`: Foreign key to Supplier model
  - `invoice_number`: Supplier's invoice number
  - `note`: Additional notes
  - `week`, `year`: For planning purchases
  - `subtotal`, `global_discount`, `total`: Financial calculations
  - `status`: draft, confirmed, received, cancelled
  - `created_by`: User who created the order
  - Dates: `order_date`, `confirmed_date`, `received_date`

- **PurchaseOrderItem**: Line items in purchase order
  - `purchase_order`: Foreign key to PurchaseOrder
  - `product`: Foreign key to Product model
  - `reference`, `designation`: Product details
  - `unit_price_ht`, `quantity`, `discount`, `total_ht`
  - `received_quantity`: Track partial deliveries

### 2. Serializers (`purchases/serializers.py`)
- **PurchaseOrderSerializer**: Full serializer with nested items
- **PurchaseOrderItemSerializer**: For individual line items
- **PurchaseOrderCreateSerializer**: Simplified for frontend data structure
  - Handles frontend field names (camelCase to snake_case)
  - Creates nested items automatically
  - Updates supplier orders count

### 3. Views (`purchases/views.py`)
- **PurchaseOrderViewSet**: Complete CRUD operations
  - `list`: Get all purchase orders (with filters)
  - `create`: Create new purchase order
  - `retrieve`: Get single purchase order
  - `update`: Update purchase order
  - `destroy`: Delete purchase order
  
  Custom actions:
  - `confirm`: Change status from draft to confirmed
  - `mark_received`: Mark as received and update product stock
  - `cancel`: Cancel order
  - `stats`: Get purchase statistics

- **PurchaseOrderItemViewSet**: Manage individual items

### 4. URLs (`purchases/urls.py`)
- `/api/purchase-orders/` - List and create orders
- `/api/purchase-orders/{id}/` - Retrieve, update, delete order
- `/api/purchase-orders/{id}/confirm/` - Confirm order
- `/api/purchase-orders/{id}/mark_received/` - Mark as received
- `/api/purchase-orders/{id}/cancel/` - Cancel order
- `/api/purchase-orders/stats/` - Get statistics

### 5. Admin (`purchases/admin.py`)
- Configured admin interface with inline items
- Admin actions:
  - Mark as confirmed
  - Mark as received (updates stock)
  - Cancel order
- Search and filters for easy management

## Database Migration
✅ Migrations created and applied successfully:
- `python manage.py makemigrations purchases`
- `python manage.py migrate purchases`

## Settings Updates
✅ Added 'purchases' to INSTALLED_APPS in settings.py
✅ Added URL patterns in main urls.py

## Frontend Integration
✅ Updated `app/admin/achats/page.tsx`:
- Connected `handleSave()` to POST `/api/purchase-orders/`
- Added useEffect to load existing orders on page load
- Updated display to show backend data structure:
  - order_number, supplier_name, status
  - invoice_number, order_date
  - Status badges (Confirmé, Reçu, Annulé)

## API Endpoints

### Create Purchase Order
```http
POST /api/purchase-orders/
Authorization: Bearer {token}
Content-Type: application/json

{
  "supplier": 1,
  "note": "Commande urgente",
  "invoiceNumber": "F-2024-001",
  "week": "3",
  "year": "2024",
  "globalDiscount": 5.00,
  "total": 1500.000,
  "items": [
    {
      "id": 123,
      "reference": "205/55R16",
      "designation": "Michelin Primacy 4",
      "priceHT": 150.000,
      "quantity": 10,
      "discount": 0,
      "totalHT": 1500.000
    }
  ]
}
```

### List Purchase Orders
```http
GET /api/purchase-orders/
Authorization: Bearer {token}

# Filters available:
?status=confirmed
?supplier=1
?week=3&year=2024
```

### Get Single Order
```http
GET /api/purchase-orders/{id}/
Authorization: Bearer {token}
```

### Confirm Order
```http
POST /api/purchase-orders/{id}/confirm/
Authorization: Bearer {token}
```

### Mark as Received (Updates Stock)
```http
POST /api/purchase-orders/{id}/mark_received/
Authorization: Bearer {token}
```

### Cancel Order
```http
POST /api/purchase-orders/{id}/cancel/
Authorization: Bearer {token}
```

### Get Statistics
```http
GET /api/purchase-orders/stats/
Authorization: Bearer {token}
```

## Features

### Auto-Calculations
- Order numbers auto-generated: ACH-202401-0001, ACH-202401-0002, etc.
- Item totals calculated automatically: (price × qty) - (discount%)
- Order total recalculated when items change

### Status Workflow
1. **draft** → Create new order
2. **confirmed** → Order confirmed with supplier
3. **received** → Delivery received, stock updated automatically
4. **cancelled** → Order cancelled

### Stock Management
- When order status changes to "received"
- System automatically updates Product.stock
- Uses `received_quantity` if set, otherwise `quantity`
- Supports partial deliveries

### Data Integrity
- PROTECT on FK deletes (can't delete supplier/product with existing orders)
- CASCADE on PurchaseOrder delete (removes items automatically)
- French verbose names for admin interface
- Decimal precision: 3 places for Tunisian Dinar

## Business Logic

This is the BUYING side of inventory management:
- **Achats (Purchases)**: Company BUYS FROM suppliers
- **Orders (Ventes)**: Company SELLS TO clients

Flow:
1. Create purchase order from supplier
2. Confirm order
3. Receive delivery
4. Stock automatically updated
5. Products now available to sell to clients

## Testing

To test the complete flow:

1. **Login to admin panel**
   ```
   Navigate to http://localhost:8000/admin/
   ```

2. **Create a purchase order via API**
   - Use the frontend at `/admin/achats`
   - Or use Postman/curl with the API

3. **Verify in admin**
   - Check Purchases → Purchase Orders
   - View created order with items

4. **Mark as received**
   - Use admin action or API endpoint
   - Check that product stock increased

5. **View statistics**
   - GET /api/purchase-orders/stats/

## Next Steps

Optional enhancements:
- [ ] PDF generation for purchase orders
- [ ] Email notifications to suppliers
- [ ] Partial delivery tracking
- [ ] Purchase order templates
- [ ] Supplier performance analytics
- [ ] Low stock alerts triggering purchase suggestions
- [ ] Purchase order approval workflow
- [ ] Integration with accounting system

## Notes

- All prices use 3 decimal places (Tunisian Dinar standard)
- Order numbers include year/month for easy identification
- System prevents deleting suppliers/products with purchase history
- Week-based planning (1-52) helps with inventory forecasting
- Created_by field tracks which user made the purchase
