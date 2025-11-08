#!/usr/bin/env python
"""
Script to create a superuser for Django admin
Run with: python manage.py shell < scripts/setup_admin.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneushop.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    """Create superuser if it doesn't exist"""
    email = 'admin@pneushop.tn'
    username = 'admin'
    password = 'admin123'
    
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"Superuser created: {email}")
        print(f"Password: {password}")
    else:
        print("Superuser already exists")

if __name__ == '__main__':
    create_superuser()
