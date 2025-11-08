# PneuShop Backend

Django REST API backend for the PneuShop tire e-commerce platform.

## Features

- **User Authentication**: Custom user model with role-based permissions
- **Product Management**: Tire products with categories, seasons, and specifications
- **Cart System**: Shopping cart functionality with session management
- **Order Processing**: Complete order workflow with delivery tracking
- **Excel Import**: Bulk product import from Excel files with image processing
- **Favorites**: User wishlist functionality
- **Supplier Management**: Supplier and purchase order tracking

## Technology Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **Database**: PostgreSQL (production), SQLite (development)
- **Image Storage**: Cloudinary
- **Server**: Gunicorn WSGI server
- **Deployment**: Docker containerization

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL (for production)
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**

   Create a `.env` file in the project root:

   ```env
   # Database Configuration
   DB_NAME=your_database_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432

   # Django Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Cloudinary Configuration
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret

   # Email Configuration
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password
   ```

5. **Database Setup**

   ```bash
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate

   # Create superuser
   python manage.py createsuperuser
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
backend/
├── accounts/           # User authentication and management
├── cart/              # Shopping cart functionality
├── favorites/         # User favorites/wishlist
├── orders/           # Order processing and tracking
├── products/         # Product management and Excel import
├── suppliers/        # Supplier management
├── pneushop/         # Main Django settings
├── scripts/          # Utility scripts
├── templates/        # Email templates
├── media/           # User uploads (not tracked in git)
├── requirements.txt  # Python dependencies
├── manage.py        # Django management script
└── gunicorn_config.py # Production server configuration
```

## API Endpoints

### Authentication

- `POST /api/accounts/register/` - User registration
- `POST /api/accounts/login/` - User login
- `POST /api/accounts/logout/` - User logout

### Products

- `GET /api/products/` - List products
- `GET /api/products/{id}/` - Product detail
- `POST /api/products/import/excel/` - Excel import
- `GET /api/products/categories/` - List categories

### Cart

- `GET /api/cart/` - Get user cart
- `POST /api/cart/add/` - Add item to cart
- `PUT /api/cart/update/{id}/` - Update cart item
- `DELETE /api/cart/remove/{id}/` - Remove from cart

### Orders

- `POST /api/orders/create/` - Create order
- `GET /api/orders/` - List user orders
- `GET /api/orders/{id}/` - Order detail

## Excel Import Feature

The system supports bulk product import via Excel files with the following format:

| NOM (Product Name)             | PRIX TTC (Price) | DESCRIPTION (Optional) |
| ------------------------------ | ---------------- | ---------------------- |
| Pneu CONTINENTAL 195/65R15 91H | 299.238          | Product description... |

Features:

- Automatic tire information extraction (brand, size, season)
- Image processing from embedded Excel images
- Cloudinary upload integration
- Batch processing for large files
- Error handling and validation

## Deployment

### Production Settings

1. **Environment Variables**

   ```env
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,your-ip-address
   ```

2. **Gunicorn Configuration**

   ```bash
   gunicorn --config gunicorn_config.py pneushop.wsgi:application
   ```

3. **Docker Deployment**
   ```bash
   docker build -t pneushop-backend .
   docker run -p 8000:8000 pneushop-backend
   ```

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test products
python manage.py test cart

# Test Excel import functionality
python test_cart_system.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Your License Here]

## Support

For support and questions, please contact [your-email@example.com]
