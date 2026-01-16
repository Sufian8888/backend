from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user, verification_code, frontend_url):
    """Send email verification with code"""
    try:
        subject = 'Vérifiez votre email - PneuShop'
        
        # Create verification URL
        verification_url = f"{frontend_url}/auth/verify-email?user_id={user.id}&code={verification_code}"
        
        # Render HTML email template
        html_content = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_code': verification_code,
            'verification_url': verification_url,
            'site_name': 'PneuShop',
            'site_url': frontend_url
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def send_welcome_email(user):
    """Send welcome email to newly registered user"""
    try:
        subject = 'Bienvenue chez PneuShop !'
        
        # Get frontend URL from settings
        frontend_url = settings.FRONTEND_URL
        
        # Render HTML email template
        html_content = render_to_string('emails/welcome_email.html', {
            'user': user,
            'site_name': 'PneuShop',
            'site_url': frontend_url
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_url, token, request_ip=None):
    """Send password reset email with secure token"""
    try:
        subject = 'Réinitialisation de votre mot de passe PneuShop'
        
        # Render HTML email template
        html_content = render_to_string('emails/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'token': token,
            'timestamp': timezone.now(),
            'request_ip': request_ip,
            'site_name': 'PneuShop'
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def send_order_confirmation_email(order):
    """Send order confirmation email with HTML template"""
    try:
        subject = f'Confirmation de commande n°{order.id} - PneuShop'
        
        # Get frontend URL from settings
        frontend_url = settings.FRONTEND_URL
        
        # Calculate subtotal (total before delivery cost)
        subtotal = order.total_amount - (order.delivery_cost or 0)
        
        # Render HTML email template
        html_content = render_to_string('emails/order_confirmation_email.html', {
            'order': order,
            'site_url': frontend_url,
            'site_name': 'PneuShop',
            'subtotal': subtotal
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Order confirmation email sent to {order.user.email} for order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.id}: {str(e)}")
        return False