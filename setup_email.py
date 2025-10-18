#!/usr/bin/env python3
"""
🛞 PneuShop Email Setup Script
This script helps you configure real email sending for the PneuShop application.
"""

import os
import sys

def main():
    print("🛞 PNEU SHOP - EMAIL SETUP")
    print("=" * 50)
    print("Setting up real email delivery to users' inboxes")
    print()
    
    print("📋 Available Email Providers:")
    print("1. Gmail (Recommended for testing)")
    print("2. SendGrid (Professional service)")
    print("3. Outlook/Hotmail")
    print("4. Keep console backend (for development)")
    print()
    
    choice = input("Choose your email provider (1-4): ").strip()
    
    env_content = []
    
    if choice == "1":
        print("\n📧 GMAIL SETUP")
        print("Follow these steps:")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Enable 2-Step Verification")
        print("3. Go to 'App passwords' and generate one for 'Django'")
        print("4. Enter your details below:")
        print()
        
        email = input("Your Gmail address: ").strip()
        password = input("Your App Password (16 characters): ").strip()
        
        env_content = [
            "# Gmail SMTP Configuration",
            "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend",
            "EMAIL_HOST=smtp.gmail.com",
            "EMAIL_PORT=587",
            "EMAIL_USE_TLS=True",
            f"EMAIL_HOST_USER={email}",
            f"EMAIL_HOST_PASSWORD={password}",
            "DEFAULT_FROM_EMAIL=noreply@pneushop.tn",
        ]
    
    elif choice == "2":
        print("\n📧 SENDGRID SETUP")
        api_key = input("Your SendGrid API Key: ").strip()
        
        env_content = [
            "# SendGrid SMTP Configuration", 
            "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend",
            "EMAIL_HOST=smtp.sendgrid.net",
            "EMAIL_PORT=587",
            "EMAIL_USE_TLS=True",
            "EMAIL_HOST_USER=apikey",
            f"EMAIL_HOST_PASSWORD={api_key}",
            "DEFAULT_FROM_EMAIL=noreply@pneushop.tn",
        ]
    
    elif choice == "3":
        print("\n📧 OUTLOOK SETUP")
        email = input("Your Outlook/Hotmail address: ").strip()
        password = input("Your password: ").strip()
        
        env_content = [
            "# Outlook SMTP Configuration",
            "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend", 
            "EMAIL_HOST=smtp-mail.outlook.com",
            "EMAIL_PORT=587",
            "EMAIL_USE_TLS=True",
            f"EMAIL_HOST_USER={email}",
            f"EMAIL_HOST_PASSWORD={password}",
            "DEFAULT_FROM_EMAIL=noreply@pneushop.tn",
        ]
    
    elif choice == "4":
        env_content = [
            "# Console backend for development",
            "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend",
            "EMAIL_HOST_USER=admin@pneushop.tn",
            "DEFAULT_FROM_EMAIL=noreply@pneushop.tn",
        ]
    
    else:
        print("Invalid choice. Exiting.")
        return
    
    # Write to .env file
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content))
        f.write('\n')
    
    print("\n✅ Email configuration saved to .env file!")
    print("\n🧪 To test the email setup:")
    print("python manage.py shell")
    print(">>> from accounts.email_utils import send_welcome_email")
    print(">>> from accounts.models import CustomUser") 
    print(">>> user = CustomUser.objects.first()")
    print(">>> send_welcome_email(user)")
    print("\n🚀 Now restart your Django server to apply changes:")
    print("python manage.py runserver")

if __name__ == "__main__":
    main()