import os
import time
from decimal import Decimal
import tempfile
import pandas as pd
import re
import cloudinary.uploader
from io import BytesIO
import tempfile
from openpyxl import load_workbook
from django.conf import settings
from django.utils.text import slugify
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Category

output_folder = os.path.join(settings.MEDIA_ROOT, "uploads/images")
os.makedirs(output_folder, exist_ok=True)



def extract_tire_info(name):
    """Extract tire information from product name"""
    # Extract brand (usually at the beginning)
    brand = "Continental"  # Default brand from Excel file
    
    # Extract tire size using improved regex (format: XXX/XX RXX or XXX/XXrXX)
    size_pattern = r'(\d{3}/\d{2}\s?R?\s?\d{2})'
    size_match = re.search(size_pattern, name, re.IGNORECASE)
    size = size_match.group(1) if size_match else "Unknown"
    
    # Clean size format
    size = re.sub(r'\s+', '', size).replace('r', 'R').replace('R', 'R')
    
    # Remove common prefixes and tire size to extract product name
    clean_name = name.replace("Pneu", "").replace("CONTINENTAL", "").strip()
    
    # Remove the tire size pattern
    if size_match:
        clean_name = clean_name.replace(size_match.group(1), "").strip()    # Remove speed/load rating patterns (like 91H, 88T, etc.)
    clean_name = re.sub(r'\b\d{2,3}[A-Z]{1,2}\b', '', clean_name).strip()
    
    # Remove extra whitespace and clean up
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    
    # Extract meaningful product name
    if clean_name:
        # Remove leading/trailing non-alphanumeric characters
        clean_name = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', clean_name)
        product_name = clean_name
    else:
        product_name = "Continental Tire"
    
    return {
        'brand': brand,
        'name': product_name,
        'size': size,
        'full_name': f"{brand} {product_name} {size}".strip()
    }

def determine_season(name, description):
    """Determine tire season based on name and description"""
    text = (name + " " + str(description)).lower()
    
    if any(word in text for word in ['winter', 'hiver', 'neige', 'snow']):
        return 'winter'
    elif any(word in text for word in ['summer', 'été', 'sport']):
        return 'summer'
    else:
        return 'all_season'


# def extract_images_from_excel(excel_file):
#     """Extracts images from Excel and saves them to disk with row reference"""
#     wb = load_workbook(excel_file)
#     ws = wb.active

#     row_images = {}
#     for i, image in enumerate(ws._images, start=1):
#         row = image.anchor._from.row
#         if row not in row_images:
#             row_images[row] = []
#         row_images[row].append(image)

#     saved_images = {}
#     for row, images in row_images.items():
#         if images:
#             tire_image = images[0]  # take first image per row
#             img_bytes = tire_image._data()
#             img_name = f"row_{row}_tire.png"
#             img_path = os.path.join(output_folder, img_name)
#             with open(img_path, "wb") as f:
#                 f.write(img_bytes)
#             saved_images[row] = f"uploads/images/{img_name}"  # relative path for DB
#     #         img_bytes_io = BytesIO(img_bytes)
#     #         upload_result = cloudinary.uploader.upload(img_bytes_io, folder="pneushop/uploads/")
#     #         saved_images[row] = upload_result.get("secure_url")  # save the URL directly
#             return saved_images

# def extract_images_from_excel(excel_file):
#     """Extracts images from Excel, uploads each to Cloudinary, and returns row->URL mapping"""
#     wb = load_workbook(excel_file)
#     ws = wb.active

#     row_images = {}
#     for image in ws._images:
#         try:
#             row = image.anchor._from.row
#             if row not in row_images:
#                 row_images[row] = []
#             row_images[row].append(image)
#         except AttributeError:
#             continue

#     saved_images = {}
#     for row, images in row_images.items():
#         if images:
#             tire_image = images[0]  # only one image per row
#             img_bytes = tire_image._data()
#             img_bytes_io = BytesIO(img_bytes)

#             upload_result = cloudinary.uploader.upload(
#                 img_bytes_io,
#                 folder="pneushop/uploads/",
#                 resource_type="image"
#             )

#             saved_images[row] = upload_result.get("secure_url")  # Cloudinary URL

#     # ✅ Must be OUTSIDE the loop
#     return saved_images

def extract_images_from_excel(excel_file):
    """Extracts images from Excel, uploads each to Cloudinary, and returns row->URL mapping"""
    wb = load_workbook(excel_file, data_only=True)
    ws = wb.active

    row_images = {}
    for image in ws._images:
        try:
            row = image.anchor._from.row
            if row not in row_images:
                row_images[row] = []
            row_images[row].append(image)
        except AttributeError:
            continue

    saved_images = {}
    for row, images in row_images.items():
        if images:
            tire_image = images[0]  # one per row

            # ✅ Get raw bytes safely
            if hasattr(tire_image, "_data"):
                img_bytes = tire_image._data()
            elif hasattr(tire_image, "ref") and hasattr(tire_image.ref, "blob"):
                img_bytes = tire_image.ref.blob
            else:
                continue  # skip if neither available

            img_bytes_io = BytesIO(img_bytes)

            # ✅ Upload directly to Cloudinary with timeout protection
            try:
                import concurrent.futures
                import threading
                
                def upload_with_timeout():
                    return cloudinary.uploader.upload(
                        img_bytes_io,
                        folder="pneushop/uploads/",
                        resource_type="image",
                        timeout=10  # 10 second cloudinary timeout
                    )
                
                # Use ThreadPoolExecutor with timeout
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(upload_with_timeout)
                    try:
                        upload_result = future.result(timeout=15)  # 15 second timeout
                        saved_images[row] = upload_result.get("secure_url")
                        print(f"✅ Uploaded image for row {row}")
                    except concurrent.futures.TimeoutError:
                        print(f"⚠️ Cloudinary upload timeout for row {row}")
                        continue
                
            except Exception as e:
                # If Cloudinary upload fails (network issue, config, etc.),
                # skip the image but continue processing other rows.
                print(f"⚠️ Cloudinary upload failed for row {row}: {e}")
                continue

    return saved_images


@api_view(['POST'])
@permission_classes([AllowAny])
def import_products_excel(request):
    # Initialize variables immediately to prevent "not associated with a value" errors
    df = None
    total_rows = 0
    created_products = []
    errors = []
    row_images = {}
    
    try:
        # Validate Cloudinary configuration
        cloudinary_available = False
        try:
            import cloudinary
            
            # Check if cloudinary is properly configured via environment or settings
            cloudinary_available = bool(
                cloudinary.config().cloud_name and 
                cloudinary.config().api_key and 
                cloudinary.config().api_secret
            )
            
            if cloudinary_available:
                print("✅ Cloudinary is configured and available")
            else:
                print("⚠️ Cloudinary not fully configured - images will be skipped")
                
        except Exception as e:
            print(f"⚠️ Cloudinary validation failed: {e} - images will be skipped")
        
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        excel_file = request.FILES['file']

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)

        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            for chunk in excel_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        # Load Excel data first
        try:
            df = pd.read_excel(temp_path)
            print(f"✅ Successfully loaded Excel file with {len(df)} rows")
        except Exception as e:
            return Response({
                'error': f'Failed to read Excel file: {str(e)}',
                'note': 'Please ensure the file is a valid Excel file (.xlsx or .xls)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract images with timeout protection (reset row_images)
        
        # Check if we should process images (based on file size and server capacity)
        process_images = (df is not None and len(df) < 50)  # Only process images for smaller files
        
        if process_images:
            try:
                print("🔄 Starting image extraction from Excel...")
                row_images = extract_images_from_excel(temp_path)
                print(f"✅ Extracted {len(row_images)} images from Excel")
            except Exception as e:
                print(f"⚠️ Image extraction failed: {e}. Continuing without images.")
                row_images = {}
                import traceback
                print(f"Image extraction traceback: {traceback.format_exc()}")
        else:
            print(f"⚠️ File has {len(df)} rows - skipping image extraction to prevent timeout")
        
        # Handle both old and new column formats
        # Check if we have the original format first
        if 'Unnamed: 0' in df.columns and 'PRIX TTC' in df.columns:
            # Original format - rename for consistency
            df = df.rename(columns={'Unnamed: 0': 'NOM'})
        else:
            # New format - normalize column names
            df.columns = [str(c).strip().upper() for c in df.columns]

        required_columns = ['NOM', 'PRIX TTC']  # DESCRIPTION is optional
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            return Response({
                'error': f'Missing columns: {missing}',
                'columns_found': list(df.columns),
                'note': 'Expected columns: NOM (product name), PRIX TTC (price), DESCRIPTION (optional)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create/get default category
        category, _ = Category.objects.get_or_create(
            name='Continental',
            defaults={'slug': 'continental', 'description': 'Pneus Continental - qualité européenne'}
        )

        # Update variables (initialized earlier)
        batch_size = 20  # Process 20 rows at a time to prevent timeout
        total_rows = len(df) if df is not None else 0

        if total_rows == 0:
            return Response({
                'error': 'Excel file is empty or has no data rows',
                'summary': {'total_rows': 0, 'created': 0, 'updated': 0, 'errors': 1},
                'errors': ['No data found in Excel file']
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"🔄 Processing {total_rows} rows from Excel in batches of {batch_size}...")

        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            print(f"📦 Processing batch {batch_start//batch_size + 1}: rows {batch_start+1} to {batch_end}")
            
            # Process current batch
            for index in range(batch_start, batch_end):
                row = df.iloc[index]
                try:
                    # Skip empty rows
                    if pd.isna(row['NOM']) or pd.isna(row['PRIX TTC']):
                        continue

                    # Only print progress every 10 rows to reduce log spam
                    if (index + 1) % 10 == 0 or index == 0:
                        print(f"📝 Processing row {index + 1} of {total_rows}...")

                    # Validate and clean product data
                    product_name = str(row['NOM']).strip()
                    if not product_name or len(product_name) < 2:
                        errors.append(f"Row {index + 1}: Invalid product name")
                        continue
                        
                    price = float(row['PRIX TTC'])
                    if price <= 0:
                        errors.append(f"Row {index + 1}: Invalid price: {price}")
                        continue
                        
                except (ValueError, TypeError) as e:
                    errors.append(f"Row {index + 1}: Data validation error: {e}")
                    continue

                # Handle optional DESCRIPTION column
                description = ""
                if 'DESCRIPTION' in df.columns and not pd.isna(row['DESCRIPTION']):
                    description = str(row['DESCRIPTION'])[:500]  # Limit description length
                
                # Get image path if available
                image_path = row_images.get(index + 2, None)

                # Extract tire info & generate unique slug
                try:
                    tire_info = extract_tire_info(product_name)
                    
                    # Validate tire info
                    if not tire_info.get('name') or len(tire_info['name']) < 2:
                        tire_info['name'] = product_name[:50]  # Fallback to original name
                        
                except Exception as e:
                    print(f"⚠️ Tire info extraction failed for row {index + 1}: {e}")
                    tire_info = {
                        'brand': 'Continental',
                        'name': product_name[:50],
                        'size': 'Unknown',
                        'full_name': product_name[:50]
                    }

                # Generate unique slug
                try:
                    base_slug = slugify(tire_info['full_name'])
                    if not base_slug:  # If slugify returns empty string
                        base_slug = f"product-{index}"
                        
                    slug = base_slug
                    counter = 1
                    while Product.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                        
                except Exception as e:
                    slug = f"product-{index}-{int(time.time())}"  # Fallback unique slug
                    print(f"⚠️ Slug generation failed for row {index + 1}: {e}, using fallback: {slug}")

                # Determine season
                try:
                    season = determine_season(product_name, description)
                except Exception as e:
                    season = 'all_season'  # Safe fallback
                    print(f"⚠️ Season determination failed for row {index + 1}: {e}")

                # Create product with error handling
                try:
                    product = Product.objects.create(
                        name=tire_info['name'][:100],  # Ensure field length limits
                        brand=tire_info['brand'][:50],
                        size=tire_info['size'][:20],
                        slug=slug,
                        description=description[:500],
                        price=Decimal(str(price)),
                        category=category,
                        season=season,
                        stock=10,
                        is_active=True,
                        image=image_path or ""  # Handle None image_path
                    )
                    created_products.append(product.name)
                    print(f"✅ Created product: {product.name}")
                    
                except Exception as db_error:
                    error_msg = f"Row {index + 1}: Database error creating product: {db_error}"
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
                    continue

                except Exception as e:
                    error_msg = f"Row {index + 1}: Unexpected error: {e}"
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
                    import traceback
                    print(f"Full traceback: {traceback.format_exc()}")
                    continue
            
            # Print batch completion
            print(f"✅ Completed batch {batch_start//batch_size + 1} - Created {len(created_products)} products so far")

        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except Exception as e:
            print(f"⚠️ Could not delete temp file {temp_path}: {e}")

        # Calculate success rate
        success_rate = (len(created_products) / total_rows * 100) if total_rows > 0 else 0
        
        response_data = {
            'message': '✅ Import completed successfully',
            'summary': {
                'total_rows': total_rows,
                'created': len(created_products),
                'updated': 0,  # Add for frontend compatibility
                'errors': len(errors),
                'success_rate': f"{success_rate:.1f}%",
                'processing_time': 'Processed in batches to prevent timeout',
                'images_processed': len(row_images) > 0
            },
            'created_products': created_products[:50],  # Limit response size
            'updated_products': [],  # Add for frontend compatibility
            'errors': errors[:20],  # Limit error list
            'note': 'Large files are processed in batches to prevent server timeout'
        }
        
        response = Response(response_data)
        # Explicitly add CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    except Exception as e:
        # More detailed error for debugging
        import traceback
        error_detail = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"❌ Import failed: {error_detail}")
        return Response(error_detail, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def import_products_fast(request):
    """Fast import for large files - minimal processing, no images"""
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        excel_file = request.FILES['file']
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)

        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            for chunk in excel_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        # Load Excel data
        df = pd.read_excel(temp_path)
        
        # Handle column formats
        if 'Unnamed: 0' in df.columns:
            df = df.rename(columns={'Unnamed: 0': 'NOM'})
        else:
            df.columns = [str(c).strip().upper() for c in df.columns]

        # Get/create category
        category, _ = Category.objects.get_or_create(
            name='Continental',
            defaults={'slug': 'continental', 'description': 'Imported products'}
        )

        created_products, errors = [], []
        batch_size = 50  # Larger batches for faster processing
        
        # Bulk create products for speed
        products_to_create = []
        
        for index, row in df.iterrows():
            try:
                if pd.isna(row.get('NOM')) or pd.isna(row.get('PRIX TTC')):
                    continue
                    
                product_name = str(row['NOM']).strip()[:100]
                price = float(row['PRIX TTC'])
                
                # Simple slug generation
                slug = slugify(product_name)
                if not slug:
                    slug = f"product-{index}"
                    
                # Make slug unique with counter
                counter = 1
                original_slug = slug
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                
                # Create product object (don't save yet)
                products_to_create.append(Product(
                    name=product_name,
                    brand='Continental',
                    size='Unknown',
                    slug=slug,
                    description=str(row.get('DESCRIPTION', ''))[:500],
                    price=Decimal(str(price)),
                    category=category,
                    season='all_season',
                    stock=10,
                    is_active=True,
                    image=""
                ))
                
                # Bulk create every 50 products
                if len(products_to_create) >= batch_size:
                    Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
                    created_products.extend([p.name for p in products_to_create])
                    products_to_create = []
                    print(f"✅ Created batch of {batch_size} products")
                    
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                continue
        
        # Create remaining products
        if products_to_create:
            Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
            created_products.extend([p.name for p in products_to_create])

        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass

        response = Response({
            'message': '🚀 Fast import completed successfully',
            'summary': {
                'total_rows': len(df),
                'created': len(created_products),
                'errors': len(errors),
                'processing_method': 'Bulk create for maximum speed',
                'images_processed': False
            },
            'created_products': created_products[:20],
            'errors': errors[:10]
        })
        
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def quick_import_test(request):
    """Quick test import without images - for debugging deployment"""
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        excel_file = request.FILES['file']
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)

        # Save temporarily and read Excel without image processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            for chunk in excel_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        # Load Excel data
        df = pd.read_excel(temp_path)
        
        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass

        response = Response({
            'message': '✅ Quick test successful - Excel file processed without images',
            'columns_found': list(df.columns),
            'total_rows': len(df),
            'first_3_rows': df.head(3).to_dict('records') if len(df) > 0 else [],
            'note': 'This is a test endpoint - no products were created'
        })
        
        # Add CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response

    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def import_preview(request):
    """Preview Excel file data before import and test API connectivity"""
    
    # Test database connection
    try:
        category_count = Category.objects.count()
        product_count = Product.objects.count()
        db_status = f"✅ Database connected - {category_count} categories, {product_count} products"
    except Exception as e:
        db_status = f"❌ Database error: {e}"
    
    # Test Cloudinary
    try:
        import cloudinary
        cloudinary_status = f"✅ Cloudinary config: {bool(cloudinary.config().cloud_name)}"
    except Exception as e:
        cloudinary_status = f"❌ Cloudinary error: {e}"
    
    return Response({
        'message': 'Import API is ready',
        'status': {
            'database': db_status,
            'cloudinary': cloudinary_status,
            'api_endpoint': '✅ API responding correctly'
        },
        'expected_format': {
            'method': 'POST',
            'content_type': 'multipart/form-data',
            'file_field': 'file',
            'supported_formats': ['.xlsx', '.xls'],
            'columns': ['NOM (or Unnamed: 0)', 'PRIX TTC', 'DESCRIPTION (optional)'],
            'example': {
                'NOM': 'Pneu CONTINENTAL 195/65R15 91H ULTRA CONTACT',
                'PRIX TTC': 299.238,
                'DESCRIPTION': 'Points forts: Kilométrage ultra-élevé...'
            }
        }
    })
