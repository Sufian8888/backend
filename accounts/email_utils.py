from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    """Send welcome email to newly registered user"""
    try:
        subject = 'Bienvenue chez PneuShop !'
        
        # Render HTML email template
        html_content = render_to_string('emails/welcome_email.html', {
            'user': user,
            'site_name': 'PneuShop',
            'site_url': 'http://localhost:3000'
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

def send_order_confirmation_email(user, order):
    """Send order confirmation email (bonus feature)"""
    try:
        subject = f'Confirmation de commande #{order.id} - PneuShop'
        
        # Simple text email for order confirmation
        message = f"""
Bonjour {user.first_name or user.username},

Votre commande #{order.id} a été confirmée avec succès !

Détails de la commande :
- Total : {order.total_amount} DT
- Date : {order.created_at.strftime('%d/%m/%Y à %H:%M')}

Nous vous tiendrons informé du statut de votre commande.

Merci de votre confiance,
L'équipe PneuShop
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Order confirmation email sent to {user.email} for order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {str(e)}")
        return False