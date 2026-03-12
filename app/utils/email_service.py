"""
Email service for sending emails via Mailgun API.
"""
import os
import requests
import logging
from flask import url_for

logger = logging.getLogger(__name__)


def _get_mailgun_config():
    """Get Mailgun configuration from environment variables."""
    api_key = os.getenv('MAILGUN_API_KEY', '').strip()
    custom_domain = os.getenv('CUSTOM_DOMAIN', '').strip()
    sender_email = os.getenv('SENDER_EMAIL', '').strip()

    if not api_key:
        raise ValueError("MAILGUN_API_KEY environment variable is not set")
    if not custom_domain:
        raise ValueError("CUSTOM_DOMAIN environment variable is not set")
    if not sender_email:
        raise ValueError("SENDER_EMAIL environment variable is not set")

    return {
        'api_key': api_key,
        'domain': custom_domain,
        'sender_email': sender_email
    }


def send_email(to_email, subject, text_content, html_content=None, app_name=None):
    """
    Send an email using Mailgun API.

    Args:
        to_email: Recipient email address
        subject: Email subject
        text_content: Plain text email content
        html_content: Optional HTML email content
        app_name: Display name for "From" (defaults to "March Madness Pool")

    Returns:
        requests.Response object if successful

    Raises:
        ValueError: If required environment variables are missing
        requests.exceptions.RequestException: If email sending fails
    """
    config = _get_mailgun_config()
    display_name = app_name or "March Madness Pool"

    data = {
        "from": f"{display_name} <{config['sender_email']}>",
        "to": to_email,
        "subject": subject,
        "text": text_content
    }

    if html_content:
        data["html"] = html_content

    response = requests.post(
        f"https://api.mailgun.net/v3/{config['domain']}/messages",
        auth=("api", config['api_key']),
        data=data
    )
    response.raise_for_status()
    logger.info(f"Email sent successfully to {to_email}")
    return response


def send_password_reset_email(user, token, app_name=None, reset_route_name='reset_password'):
    """
    Send password reset email to a user.

    Args:
        user: User model instance (must have .email)
        token: Password reset token string
        app_name: Display name for emails (defaults to "March Madness Pool")
        reset_route_name: Flask route name for reset (e.g. 'reset_password')

    Returns:
        requests.Response if successful, None if error (logged)

    Note: Must be called within a Flask application context.
    """
    reset_url = url_for(reset_route_name, token=token, _external=True)
    display_name = app_name or "March Madness Pool"

    subject = "Reset Your Password"

    text_content = f"""Hello,

You requested to reset your password. Click the link below to reset it:

{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

Best regards,
{display_name}
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Reset Your Password</h2>
        <p>Hello,</p>
        <p>You requested to reset your password. Click the button below to reset it:</p>
        <a href="{reset_url}" style="display: inline-block; padding: 12px 24px; background-color: #28a745; color: #ffffff !important; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; text-align: center;">Reset Password</a>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666;">{reset_url}</p>
        <p>This link will expire in 1 hour.</p>
        <p>If you did not request a password reset, please ignore this email. Your password will remain unchanged.</p>
        <div class="footer">
            <p>Best regards,<br>{display_name}</p>
        </div>
    </div>
</body>
</html>
"""

    try:
        return send_email(
            to_email=user.email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            app_name=display_name
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return None


def send_password_reset_confirmation_email(user, app_name=None):
    """
    Send confirmation email after password has been successfully reset.
    """
    display_name = app_name or "March Madness Pool"
    subject = "Your Password Has Been Reset"

    text_content = f"""Hello,

Your password has been successfully reset.

If you did not reset your password, please contact us immediately.

Best regards,
{display_name}
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Your Password Has Been Reset</h2>
        <p>Hello,</p>
        <p>Your password has been successfully reset.</p>
        <p>If you did not reset your password, please contact us immediately.</p>
        <div class="footer">
            <p>Best regards,<br>{display_name}</p>
        </div>
    </div>
</body>
</html>
"""

    try:
        return send_email(
            to_email=user.email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            app_name=display_name
        )
    except Exception as e:
        logger.error(f"Failed to send password reset confirmation email to {user.email}: {e}")
        return None
