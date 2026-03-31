import os
import time
from decimal import Decimal
import tempfile
import uuid
import pandas as pd
import re
import cloudinary.uploader
from io import BytesIO
from openpyxl import load_workbook
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import close_old_connections
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Category, ImportJob
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import traceback

output_folder = os.path.join(settings.MEDIA_ROOT, "uploads/images")
os.makedirs(output_folder, exist_ok=True)



def extract_tire_info(name):
    """Extract tire information from product name"""
    print(f"🔍 Extracting tire info from: {name}")
    
    # Extract brand dynamically: first word after PNEU / TIRE / TYRE prefix
    # e.g. "PNEU AMINE 175/70R14" → "Amine"
    #      "PNEU CONTINENTAL 205/55R16" → "Continental"
    name_clean = re.sub(r'^(PNEU|TIRE|TYRE)\s+', '', name.strip(), flags=re.IGNORECASE)
    first_word = name_clean.split()[0] if name_clean.split() else None
    if first_word and re.match(r'^[A-Za-z]+$', first_word):
        brand = first_word.capitalize()
    else:
        brand = "Unknown"
    
    # Extract tire size using improved regex (format: XXX/XX RXX or XXX/XXrXX)
    # Updated to handle more variations: 165/60R14, 195/65 R 15, 205/55R16, etc.
    size_pattern = r'(\d{2,3}[/]\d{2}\s?[RrXx]?\s?\d{1,2})'
    size_match = re.search(size_pattern, name, re.IGNORECASE)
    size = size_match.group(1) if size_match else "Unknown"
    
    # Clean size format
    if size != "Unknown":
        size = re.sub(r'\s+', '', size).upper().replace('r', 'R').replace('X', 'R')
        if 'R' not in size and '/' in size:
            # Add R if missing (e.g., 205/55 16 -> 205/55R16)
            parts = size.split('/')
            if len(parts) == 2:
                size = f"{parts[0]}/{parts[1][:2]}R{parts[1][2:]}"
    
    print(f"   Brand: {brand}, Size: {size}")
    
    # Remove common prefixes and tire size to extract product name
    clean_name = re.sub(r'^(PNEU|TIRE|TYRE)\s+', '', name.strip(), flags=re.IGNORECASE)
    
    # Remove the detected brand word from the name
    clean_name = re.sub(r'^' + re.escape(brand) + r'\s+', '', clean_name, flags=re.IGNORECASE).strip()
    
    # Remove the tire size pattern
    if size_match:
        clean_name = clean_name.replace(size_match.group(1), "").strip()
    
    # Remove speed/load rating patterns (like 91H, 88T, 75H XL, etc.)
    clean_name = re.sub(r'\b\d{2,3}\s?[A-Z]{1,2}\s?(XL|RF|C)?\b', '', clean_name, flags=re.IGNORECASE).strip()
    
    # Remove extra whitespace and clean up
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    
    # Extract meaningful product name
    if clean_name:
        # Remove leading/trailing non-alphanumeric characters
        clean_name = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', clean_name)
        product_name = clean_name if clean_name else name[:50]
    else:
        product_name = name[:50]
    
    full_name = f"{brand} {product_name} {size}".strip()
    print(f"   Result: {full_name}")
    
    return {
        'brand': brand,
        'name': product_name,
        'size': size,
        'full_name': full_name
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

def determine_category(name, description):
    """Determine product category from name and description"""
    text = (str(name) + " " + str(description)).lower()
    
    # ONLY these 5 categories are allowed
    VALID_CATEGORIES = ['tourisme', '4x4', 'agricole', 'utilitaire', 'moto']
    
    # Category keywords mapping
    category_keywords = {
        'tourisme': ['tourisme', 'tourism', 'passenger', 'car', 'voiture'],
        '4x4': ['4x4', '4wd', 'suv', 'tout-terrain', 'off-road'],
        'agricole': ['agricole', 'agricultural', 'farm', 'tracteur', 'tractor'],
        'utilitaire': ['utilitaire', 'utility', 'commercial', 'van', 'fourgon', 'camionnette'],
        'moto': ['moto', 'motorcycle', 'scooter', 'bike']
    }
    
    # Check for category keywords
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    # Default to tourisme if no category found
    return 'tourisme'


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

def extract_images_from_excel_optimized(excel_file):
    """
    ⚡ OPTIMIZED: Extracts images from Excel and uploads to Cloudinary IN PARALLEL
    Instead of: 30 seconds per image × 33 images = 16+ minutes
    Now: 30 seconds for ALL images in parallel = 30-40 seconds total!
    """
    wb = load_workbook(excel_file, data_only=True)
    
    all_saved_images = {}
    all_images_to_upload = []  # Queue of (row, image, idx)
    row_offset = 0
    
    # STEP 1: Collect all images to upload (fast - no uploads yet)
    print("🔄 Step 1: Extracting images from Excel sheets...")
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
        row_images = {}
        for image in ws._images:
            try:
                row = image.anchor._from.row
                if row not in row_images:
                    row_images[row] = []
                row_images[row].append(image)
            except AttributeError:
                continue

        # Collect all images (don't upload yet)
        for row, images in row_images.items():
            if images:
                for idx, tire_image in enumerate(images[:3]):  # Max 3 images
                    all_images_to_upload.append((row + row_offset, tire_image, idx))
        
        row_offset += ws.max_row

    print(f"📦 Found {len(all_images_to_upload)} images to upload")

    # STEP 2: Upload all images IN PARALLEL using ThreadPoolExecutor
    print("🚀 Step 2: Uploading to Cloudinary in parallel (5 concurrent threads)...")
    
    uploaded_mapping = {}  # {(row, idx): url}
    lock = threading.Lock()
    
    def upload_single_image(args):
        """Upload a single image to Cloudinary"""
        row, tire_image, idx = args
        try:
            img_bytes = tire_image._data()
            img_bytes_io = BytesIO(img_bytes)
            
            upload_result = cloudinary.uploader.upload(
                img_bytes_io,
                folder="pneushop/uploads/",
                resource_type="image",
                timeout=60
            )
            
            url = upload_result.get("secure_url")
            with lock:
                uploaded_mapping[(row, idx)] = url
            
            print(f"✅ Uploaded image for row {row}, index {idx}")
            return (row, idx, url)
            
        except Exception as e:
            print(f"❌ Failed to upload image for row {row}, idx {idx}: {e}")
            return None

    # Use ThreadPoolExecutor with 5 concurrent threads
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_single_image, img_args) for img_args in all_images_to_upload]
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            if completed % 5 == 0:
                print(f"Progress: {completed}/{len(all_images_to_upload)} images uploaded")
    
    upload_time = time.time() - start_time
    print(f"⏱️ Total upload time: {upload_time:.1f} seconds for {len(all_images_to_upload)} images")

    # STEP 3: Organize results by row
    print("🔄 Step 3: Organizing results...")
    for row, idx in uploaded_mapping:
        if row not in all_saved_images:
            all_saved_images[row] = []
        all_saved_images[row].insert(idx, uploaded_mapping[(row, idx)])

    print(f"✅ Extracted and uploaded {sum(len(urls) for urls in all_saved_images.values())} images from {len(all_saved_images)} products")
    print(f"⏰ Total time: {upload_time:.1f}s | Speed: {len(all_images_to_upload)/upload_time:.1f} images/sec")
    return all_saved_images


# Keep old function for backwards compatibility
def extract_images_from_excel(excel_file):
    """Wrapper - uses optimized parallel version"""
    return extract_images_from_excel_optimized(excel_file)


def _save_uploaded_import_file(uploaded_file):
    """Save uploaded file to persistent import folder and return absolute path."""
    import_dir = os.path.join(settings.MEDIA_ROOT, "uploads/imports")
    os.makedirs(import_dir, exist_ok=True)

    storage = FileSystemStorage(location=import_dir)
    safe_name = os.path.basename(uploaded_file.name)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    stored_name = storage.save(unique_name, uploaded_file)
    return storage.path(stored_name)


def _run_excel_import(file_path, job=None):
    """Run full import logic and return summary data for async job updates."""
    df = None
    created_products = []
    errors = []
    row_images = {}

    # Validate Cloudinary configuration
    cloudinary_available = False
    try:
        import cloudinary
        cloudinary_available = bool(
            cloudinary.config().cloud_name
            and cloudinary.config().api_key
            and cloudinary.config().api_secret
        )
        if cloudinary_available:
            print("✅ Cloudinary is configured and available")
        else:
            print("⚠️ Cloudinary not fully configured - images will be skipped")
    except Exception as e:
        print(f"⚠️ Cloudinary validation failed: {e} - images will be skipped")

    # Load Excel data first - handle multiple sheets
    excel_data = pd.read_excel(file_path, sheet_name=None)
    if not excel_data:
        raise ValueError("Excel file has no sheets")

    # Combine all sheets into one dataframe
    df = pd.concat(excel_data.values(), ignore_index=True)
    sheet_count = len(excel_data)
    print(f"✅ Successfully loaded Excel file with {sheet_count} sheet(s) and {len(df)} total rows")

    # Extract images (if cloudinary is available)
    if cloudinary_available:
        try:
            print("🔄 Starting image extraction from Excel...")
            row_images = extract_images_from_excel(file_path)
            print(f"✅ Extracted {len(row_images)} images from Excel")
        except Exception as e:
            print(f"⚠️ Image extraction failed: {e}. Continuing without images.")
            row_images = {}
            print(f"Image extraction traceback: {traceback.format_exc()}")

    # Normalize column names
    df.columns = [str(c).strip().upper() for c in df.columns]

    if 'REFERNECE' in df.columns:
        df = df.rename(columns={'REFERNECE': 'REFERENCE'})

    if 'UNNAMED: 0' in df.columns:
        if 'REFERENCE' not in df.columns and 'NOM' not in df.columns:
            df = df.rename(columns={'UNNAMED: 0': 'NOM'})
        else:
            df = df.drop(columns=['UNNAMED: 0'])

    # Required: either NOM or REFERENCE, and PRIX TTC
    has_name = 'NOM' in df.columns or 'REFERENCE' in df.columns
    has_price = 'PRIX TTC' in df.columns

    if not has_price:
        raise ValueError('Missing required column: PRIX TTC')

    if not has_name:
        raise ValueError('Missing product name column (expected NOM or REFERENCE)')

    batch_size = 20
    total_rows = len(df) if df is not None else 0

    if total_rows == 0:
        raise ValueError('Excel file is empty or has no data rows')

    print(f"🔄 Processing {total_rows} rows from Excel in batches of {batch_size}...")

    if job:
        job.total_rows = total_rows
        job.created_count = 0
        job.error_count = 0
        job.message = f"Upload completed. Processing 0/{total_rows} rows..."
        job.save(update_fields=['total_rows', 'created_count', 'error_count', 'message', 'updated_at'])

    processed_rows = 0
    last_progress_save = time.time()

    for batch_start in range(0, total_rows, batch_size):
        batch_end = min(batch_start + batch_size, total_rows)

        for index in range(batch_start, batch_end):
            row = df.iloc[index]
            processed_rows += 1
            try:
                product_name = None
                if 'REFERENCE' in df.columns and not pd.isna(row['REFERENCE']):
                    product_name = str(row['REFERENCE']).strip()
                elif 'NOM' in df.columns and not pd.isna(row['NOM']):
                    product_name = str(row['NOM']).strip()

                if not product_name or pd.isna(row['PRIX TTC']):
                    if job and (time.time() - last_progress_save > 0.7):
                        job.message = f"Processing row {processed_rows}/{total_rows} (empty/invalid row skipped)"
                        job.error_count = len(errors)
                        job.created_count = len(created_products)
                        job.save(update_fields=['message', 'error_count', 'created_count', 'updated_at'])
                        last_progress_save = time.time()
                    continue

                if len(product_name) < 2:
                    errors.append(f"Row {index + 1}: Invalid product name")
                    if job and (time.time() - last_progress_save > 0.7):
                        job.message = f"Processing row {processed_rows}/{total_rows} (invalid product name)"
                        job.error_count = len(errors)
                        job.created_count = len(created_products)
                        job.save(update_fields=['message', 'error_count', 'created_count', 'updated_at'])
                        last_progress_save = time.time()
                    continue

                price = float(row['PRIX TTC'])
                if price <= 0:
                    errors.append(f"Row {index + 1}: Invalid price: {price}")
                    if job and (time.time() - last_progress_save > 0.7):
                        job.message = f"Processing row {processed_rows}/{total_rows} (invalid price)"
                        job.error_count = len(errors)
                        job.created_count = len(created_products)
                        job.save(update_fields=['message', 'error_count', 'created_count', 'updated_at'])
                        last_progress_save = time.time()
                    continue

            except (ValueError, TypeError) as e:
                errors.append(f"Row {index + 1}: Data validation error: {e}")
                if job and (time.time() - last_progress_save > 0.7):
                    job.message = f"Processing row {processed_rows}/{total_rows} (data validation error)"
                    job.error_count = len(errors)
                    job.created_count = len(created_products)
                    job.save(update_fields=['message', 'error_count', 'created_count', 'updated_at'])
                    last_progress_save = time.time()
                continue

            description = ""
            if 'DESCRIPTION' in df.columns and not pd.isna(row['DESCRIPTION']):
                description = str(row['DESCRIPTION']).strip()

            image_urls = row_images.get(index + 2, [])
            image_1 = image_urls[0] if len(image_urls) > 0 else ""
            image_2 = image_urls[1] if len(image_urls) > 1 else ""
            image_3 = image_urls[2] if len(image_urls) > 2 else ""

            try:
                tire_info = extract_tire_info(product_name)
                product_display_name = product_name
            except Exception as e:
                print(f"⚠️ Tire info extraction failed for row {index + 1}: {e}")
                tire_info = {'brand': 'Laufenn', 'size': 'Unknown'}
                product_display_name = product_name

            if job and (time.time() - last_progress_save > 0.7):
                progress_title = tire_info.get('full_name', product_display_name)
                job.message = (
                    f"Processing row {processed_rows}/{total_rows} | "
                    f"Brand: {tire_info.get('brand', 'Unknown')} | "
                    f"Size: {tire_info.get('size', 'Unknown')} | "
                    f"Result: {progress_title[:120]}"
                )
                job.error_count = len(errors)
                job.created_count = len(created_products)
                job.save(update_fields=['message', 'error_count', 'created_count', 'updated_at'])
                last_progress_save = time.time()

            try:
                base_slug = slugify(product_display_name)
                if not base_slug:
                    base_slug = f"product-{index}"

                slug = base_slug
                counter = 1
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            except Exception as e:
                slug = f"product-{index}-{int(time.time())}"
                print(f"⚠️ Slug generation failed for row {index + 1}: {e}, using fallback: {slug}")

            try:
                season = determine_season(product_name, description)
            except Exception as e:
                season = 'all_season'
                print(f"⚠️ Season determination failed for row {index + 1}: {e}")

            try:
                category_name = determine_category(product_name, description)
                category_slug = slugify(category_name)

                category, _ = Category.objects.get_or_create(
                    slug=category_slug,
                    defaults={
                        'name': category_name,
                        'description': f'Pneus {category_name}'
                    }
                )
            except Exception as e:
                category, _ = Category.objects.get_or_create(
                    slug='tourisme',
                    defaults={'name': 'tourisme', 'description': 'Pneus tourisme'}
                )
                print(f"⚠️ Category determination failed for row {index + 1}: {e}")

            try:
                product = Product.objects.create(
                    name=product_display_name[:200],
                    brand=tire_info['brand'][:100],
                    size=tire_info['size'][:100],
                    slug=slug,
                    description=description,
                    price=Decimal(str(price)),
                    category=category,
                    season=season,
                    stock=10,
                    is_active=True,
                    image=image_1,
                    image_2=image_2,
                    image_3=image_3
                )
                created_products.append(product.name)

            except Exception as db_error:
                error_msg = f"Row {index + 1}: Database error creating product: {db_error}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                if job and (time.time() - last_progress_save > 0.7):
                    job.message = f"Processing row {processed_rows}/{total_rows} (database error)"
                    job.error_count = len(errors)
                    job.created_count = len(created_products)
                    job.save(update_fields=['message', 'error_count', 'created_count', 'updated_at'])
                    last_progress_save = time.time()
                continue

            if job and (time.time() - last_progress_save > 0.7):
                job.message = f"Processing row {processed_rows}/{total_rows} | Created: {len(created_products)} | Errors: {len(errors)}"
                job.error_count = len(errors)
                job.created_count = len(created_products)
                job.save(update_fields=['message', 'error_count', 'created_count', 'updated_at'])
                last_progress_save = time.time()

        print(f"✅ Completed batch {batch_start // batch_size + 1} - Created {len(created_products)} products so far")

    success_rate = (len(created_products) / total_rows * 100) if total_rows > 0 else 0

    return {
        'total_rows': total_rows,
        'created': len(created_products),
        'errors': errors,
        'error_count': len(errors),
        'images_processed': len(row_images) > 0,
        'success_rate': f"{success_rate:.1f}%"
    }


def _process_import_job(job_id):
    """Background job processor for Excel import."""
    close_old_connections()
    job = None

    try:
        job = ImportJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.message = 'Processing started'
        job.save(update_fields=['status', 'started_at', 'message', 'updated_at'])

        summary = _run_excel_import(job.file_path, job=job)

        job.status = 'completed'
        job.total_rows = summary['total_rows']
        job.created_count = summary['created']
        job.error_count = summary['error_count']
        job.images_processed = summary['images_processed']
        job.errors = summary['errors'][:50]
        job.message = f"Import completed successfully ({summary['success_rate']})"
        job.finished_at = timezone.now()
        job.save()

    except Exception as e:
        if job is None:
            try:
                job = ImportJob.objects.get(id=job_id)
            except Exception:
                return

        job.status = 'failed'
        job.message = str(e)
        job.error_count = max(job.error_count, 1)
        job.errors = [str(e), traceback.format_exc()]
        job.finished_at = timezone.now()
        job.save()

    finally:
        # Final step: always delete source file so server storage does not grow.
        try:
            if job and job.file_path and os.path.exists(job.file_path):
                os.unlink(job.file_path)
                job.file_path = ''
                job.save(update_fields=['file_path', 'updated_at'])
                print(f"🧹 Deleted processed import file for job {job.id}")
        except Exception as cleanup_error:
            print(f"⚠️ Could not delete import file for job {job_id}: {cleanup_error}")

        close_old_connections()


@api_view(['POST'])
@permission_classes([AllowAny])
def import_products_excel(request):
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        excel_file = request.FILES['file']

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)

        saved_path = _save_uploaded_import_file(excel_file)

        job = ImportJob.objects.create(
            original_filename=excel_file.name,
            file_path=saved_path,
            status='queued',
            message='File uploaded and queued for background processing.'
        )

        worker = threading.Thread(
            target=_process_import_job,
            args=(str(job.id),),
            daemon=True
        )
        worker.start()

        response = Response({
            'message': '✅ File uploaded. Import started in background.',
            'job_id': str(job.id),
            'status': job.status,
            'status_endpoint': f'/api/products/import/status/{job.id}/',
            'note': 'Upload request returns immediately. Processing continues asynchronously.'
        }, status=status.HTTP_202_ACCEPTED)

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    except Exception as e:
        error_detail = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"❌ Import failed: {error_detail}")
        return Response(error_detail, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def import_status(request, job_id):
    """Get background import status and summary."""
    job = get_object_or_404(ImportJob, id=job_id)

    response = Response({
        'job_id': str(job.id),
        'status': job.status,
        'original_filename': job.original_filename,
        'summary': {
            'total_rows': job.total_rows,
            'created': job.created_count,
            'errors': job.error_count,
            'images_processed': job.images_processed,
        },
        'message': job.message,
        'errors': job.errors[:20],
        'started_at': job.started_at,
        'finished_at': job.finished_at,
        'created_at': job.created_at,
        'updated_at': job.updated_at,
    })
    response['Access-Control-Allow-Origin'] = '*'
    return response


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


@api_view(['POST'])
@permission_classes([AllowAny])
def import_data_only_fast(request):
    """
    ⚡ FASTEST EXTRACTION: Data-only import WITHOUT image processing
    Perfect for: 11 rows takes ~5-10 seconds instead of 7-8 minutes
    """
    created_products = []
    errors = []
    
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

        try:
            # Read all sheets
            excel_data = pd.read_excel(temp_path, sheet_name=None)
            df = pd.concat(excel_data.values(), ignore_index=True)
            
            # Normalize column names
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Rename typos
            if 'REFERNECE' in df.columns:
                df = df.rename(columns={'REFERNECE': 'REFERENCE'})
            
            if 'UNNAMED: 0' in df.columns and 'REFERENCE' not in df.columns and 'NOM' not in df.columns:
                df = df.rename(columns={'UNNAMED: 0': 'NOM'})
            elif 'UNNAMED: 0' in df.columns:
                df = df.drop(columns=['UNNAMED: 0'])
                
        except Exception as e:
            return Response({
                'error': f'Failed to read Excel file: {str(e)}',
                'note': 'Please ensure the file is a valid Excel file (.xlsx or .xls)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate required columns
        has_name = 'NOM' in df.columns or 'REFERENCE' in df.columns
        has_price = 'PRIX TTC' in df.columns
        
        if not has_price or not has_name:
            return Response({
                'error': f'Missing required columns (need: NOM or REFERENCE, PRIX TTC)',
                'columns_found': list(df.columns)
            }, status=status.HTTP_400_BAD_REQUEST)

        total_rows = len(df)
        batch_size = 50

        print(f"🚀 FAST DATA-ONLY IMPORT: Processing {total_rows} rows (NO IMAGES)...")

        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            
            for index in range(batch_start, batch_end):
                row = df.iloc[index]
                try:
                    # Get product name
                    product_name = None
                    if 'REFERENCE' in df.columns and not pd.isna(row['REFERENCE']):
                        product_name = str(row['REFERENCE']).strip()
                    elif 'NOM' in df.columns and not pd.isna(row['NOM']):
                        product_name = str(row['NOM']).strip()
                    
                    if not product_name or len(product_name) < 2 or pd.isna(row['PRIX TTC']):
                        continue

                    # Get price
                    price = float(row['PRIX TTC'])
                    if price <= 0:
                        errors.append(f"Row {index + 1}: Invalid price")
                        continue

                    # Get description
                    description = ""
                    if 'DESCRIPTION' in df.columns and not pd.isna(row['DESCRIPTION']):
                        description = str(row['DESCRIPTION']).strip()
                    
                    # Extract tire info (ONE regex pass only)
                    try:
                        tire_info = extract_tire_info(product_name)
                    except Exception as e:
                        tire_info = {'brand': 'Unknown', 'size': 'Unknown'}

                    # Generate unique slug
                    base_slug = slugify(product_name)
                    if not base_slug:
                        base_slug = f"product-{index}"
                    
                    slug = base_slug
                    counter = 1
                    while Product.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    # Get/create category (minimal DB hits)
                    try:
                        season = determine_season(product_name, description)
                        category_name = determine_category(product_name, description)
                    except Exception:
                        season = 'all_season'
                        category_name = 'tourisme'

                    category_slug = slugify(category_name)
                    category, _ = Category.objects.get_or_create(
                        slug=category_slug,
                        defaults={'name': category_name}
                    )

                    # Create product WITHOUT images
                    Product.objects.create(
                        name=product_name[:200],
                        brand=tire_info['brand'][:100],
                        size=tire_info['size'][:100],
                        slug=slug,
                        description=description,
                        price=Decimal(str(price)),
                        category=category,
                        season=season,
                        stock=10,
                        is_active=True,
                        image=""  # No image
                    )
                    created_products.append(product_name)
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    continue

        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass

        response = Response({
            'message': '⚡ Fast data-only import completed',
            'speed': 'NO IMAGE PROCESSING - 5-10x faster',
            'summary': {
                'total_rows': total_rows,
                'created': len(created_products),
                'errors': len(errors),
                'success_rate': f"{(len(created_products)/total_rows*100):.1f}%" if total_rows > 0 else "0%"
            },
            'created_products': created_products,
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
