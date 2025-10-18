#!/usr/bin/env python3
"""
🛞 PneuShop Email Test Script
Test real email sending functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneushop.settings')
django.setup()

from accounts.models import CustomUser
from accounts.email_utils import send_welcome_email, send_password_reset_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

def test_email_sending():
    print("🛞 PNEU SHOP - EMAIL TESTING")
    print("=" * 50)
    
    # Get a test email
    test_email = input("Enter your real email address to test: ").strip()
    
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return
    
    print(f"\n📧 Testing email delivery to: {test_email}")
    
    # Create or get test user
    try:
        user, created = CustomUser.objects.get_or_create(
            email=test_email,
            defaults={
                'username': test_email.split('@')[0] + '_test',
                'first_name': 'Test',
                'last_name': 'User',
                'phone': '12345678'
            }
        )
        
        if created:
            user.set_password('testpassword123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing user: {user.username}")
        
        print("\n1️⃣ Testing Welcome Email...")
        try:
            send_welcome_email(user)
            print("✅ Welcome email sent successfully!")
        except Exception as e:
            print(f"❌ Welcome email failed: {e}")
        
        print("\n2️⃣ Testing Password Reset Email...")
        try:
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            send_password_reset_email(user, uid, token)
            print("✅ Password reset email sent successfully!")
        except Exception as e:
            print(f"❌ Password reset email failed: {e}")
        
        print(f"\n📨 Check your inbox at {test_email}")
        print("   - Look for emails from 'noreply@pneushop.tn'")
        print("   - Check spam folder if not in inbox")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n" + "=" * 50)
    print("💡 If emails don't arrive:")
    print("   1. Check your .env file configuration") 
    print("   2. Verify SMTP credentials are correct")
    print("   3. Check spam/junk folder")
    print("   4. Try a different email provider")

if __name__ == "__main__":
    test_email_sending()