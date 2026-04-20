from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging
from postmarker.core import PostmarkClient

logger = logging.getLogger(__name__)


def send_transactional_email(to, subject, text_body, html_body=None):
    """Send transactional email through Postmark default transactional stream."""
    try:
        if not settings.POSTMARK_API_KEY:
            logger.error("POSTMARK_API_KEY is missing. Email not sent.")
            return False

        client = PostmarkClient(server_token=settings.POSTMARK_API_KEY)
        client.emails.send(
            From=settings.DEFAULT_FROM_EMAIL,
            To=to,
            Subject=subject,
            TextBody=text_body,
            HtmlBody=html_body,
            MessageStream=settings.POSTMARK_MESSAGE_STREAM,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send transactional email to {to}: {str(e)}")
        return False

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
        
        sent = send_transactional_email(
            to=user.email,
            subject=subject,
            text_body=text_content,
            html_body=html_content,
        )
        if not sent:
            return False
        
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
        
        sent = send_transactional_email(
            to=user.email,
            subject=subject,
            text_body=text_content,
            html_body=html_content,
        )
        if not sent:
            return False
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_new_user_registered_admin_email(user):
    """Notify admin when a new user account is created."""
    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@pneushop.tn')
        subject = 'New User Registered'
        message = f"A new user has signed up: {user.email}"

        sent = send_transactional_email(
            to=admin_email,
            subject=subject,
            text_body=message,
            html_body=f"<p>{message}</p>",
        )
        if not sent:
            return False

        logger.info(f"✅ New user registration email sent to ADMIN: {admin_email} for user {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send new user registration email to admin for {user.email}: {str(e)}")
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
        
        sent = send_transactional_email(
            to=user.email,
            subject=subject,
            text_body=text_content,
            html_body=html_content,
        )
        if not sent:
            return False
        
        logger.info(f"Password reset email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def send_order_confirmation_email(order):
    """
    Send order confirmation email with HTML template
    Sends to BOTH customer AND admin
    """
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
        
        # SEND TO CUSTOMER
        customer_sent = send_transactional_email(
            to=order.user.email,
            subject=subject,
            text_body=text_content,
            html_body=html_content,
        )
        if not customer_sent:
            return False
        logger.info(f"✅ Order confirmation email sent to CUSTOMER: {order.user.email} for order #{order.id}")
        
        # SEND TO ADMIN (notification)
        admin_subject = f'🔔 Nouvelle commande n°{order.id} - {order.user.get_full_name()}'
        admin_html = render_to_string('emails/order_notification_admin.html', {
            'order': order,
            'site_url': frontend_url,
            'site_name': 'PneuShop',
            'subtotal': subtotal,
            'customer_name': order.user.get_full_name(),
            'customer_email': order.user.email,
            'customer_phone': order.user.phone_number if hasattr(order.user, 'phone_number') else 'N/A'
        })
        admin_text = strip_tags(admin_html)
        
        # Get admin email from settings
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@pneushop.tn')
        
        admin_sent = send_transactional_email(
            to=admin_email,
            subject=admin_subject,
            text_body=admin_text,
            html_body=admin_html,
        )
        if not admin_sent:
            return False
        logger.info(f"✅ Order notification email sent to ADMIN: {admin_email} for order #{order.id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.id}: {str(e)}")
        return False


def send_order_status_update_email(order, old_status):
    """
    Send email to customer when admin changes order status.
    Called on every status transition (confirmed, processing, shipped, delivered, cancelled).
    """
    # Map status codes to French labels and messages
    STATUS_LABELS = {
        'confirmed':  'Confirmée',
        'processing': 'En cours de traitement',
        'shipped':    'Expédiée',
        'delivered':  'Livrée',
        'cancelled':  'Annulée',
    }
    # Only send for meaningful transitions
    if order.status == old_status or order.status == 'pending':
        return False

    try:
        status_label = STATUS_LABELS.get(order.status, order.status)
        subject = f'Mise à jour de votre commande n°{order.order_number} - {status_label}'

        frontend_url = settings.FRONTEND_URL
        subtotal = order.total_amount - (order.delivery_cost or 0)

        html_content = render_to_string('emails/order_status_update.html', {
            'order': order,
            'status_label': status_label,
            'old_status': old_status,
            'site_url': frontend_url,
            'site_name': 'PneuShop',
            'subtotal': subtotal,
        })
        text_content = strip_tags(html_content)

        sent = send_transactional_email(
            to=order.user.email,
            subject=subject,
            text_body=text_content,
            html_body=html_content,
        )
        if not sent:
            return False
        logger.info(f"✅ Status update email sent to {order.user.email} for order #{order.id} → {order.status}")
        return True

    except Exception as e:
        logger.error(f"Failed to send status update email for order #{order.id}: {str(e)}")
        return False