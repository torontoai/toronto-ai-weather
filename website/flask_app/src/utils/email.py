"""
Email utility functions for Toronto AI Weather web application.
"""

import logging
from flask import current_app, render_template
from threading import Thread
from flask_mail import Message, Mail

logger = logging.getLogger(__name__)

# Initialize mail
mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            logger.error(f"Error sending email: {e}")

def send_email(subject, recipients, text_body, html_body, sender=None):
    """
    Send an email.
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        text_body (str): Plain text email body
        html_body (str): HTML email body
        sender (str): Sender email address
    """
    try:
        app = current_app._get_current_object()
        sender = sender or app.config['MAIL_DEFAULT_SENDER']
        
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        
        Thread(target=send_async_email, args=(app, msg)).start()
        
        return True
    except Exception as e:
        logger.error(f"Error preparing email: {e}")
        return False

def send_verification_email(user):
    """
    Send email verification link.
    
    Args:
        user: User object
    """
    try:
        from flask import url_for
        
        # Generate verification URL
        verification_url = url_for(
            'auth.verify_email',
            token=user.verification_token,
            _external=True
        )
        
        subject = "Verify your Toronto AI Weather account"
        
        # Plain text email
        text_body = f"""
        Hello {user.username},
        
        Thank you for registering with Toronto AI Weather!
        
        Please click the following link to verify your email address:
        {verification_url}
        
        If you did not register for an account, please ignore this email.
        
        Best regards,
        The Toronto AI Weather Team
        """
        
        # HTML email
        html_body = f"""
        <p>Hello {user.username},</p>
        
        <p>Thank you for registering with Toronto AI Weather!</p>
        
        <p>Please click the following link to verify your email address:</p>
        <p><a href="{verification_url}">Verify Email Address</a></p>
        
        <p>If you did not register for an account, please ignore this email.</p>
        
        <p>Best regards,<br>
        The Toronto AI Weather Team</p>
        """
        
        return send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body
        )
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False

def send_password_reset_email(user):
    """
    Send password reset link.
    
    Args:
        user: User object
    """
    try:
        from flask import url_for
        
        # Generate reset URL
        reset_url = url_for(
            'auth.reset_password',
            token=user.verification_token,
            _external=True
        )
        
        subject = "Reset your Toronto AI Weather password"
        
        # Plain text email
        text_body = f"""
        Hello {user.username},
        
        You have requested to reset your password for Toronto AI Weather.
        
        Please click the following link to reset your password:
        {reset_url}
        
        If you did not request a password reset, please ignore this email.
        
        Best regards,
        The Toronto AI Weather Team
        """
        
        # HTML email
        html_body = f"""
        <p>Hello {user.username},</p>
        
        <p>You have requested to reset your password for Toronto AI Weather.</p>
        
        <p>Please click the following link to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        
        <p>If you did not request a password reset, please ignore this email.</p>
        
        <p>Best regards,<br>
        The Toronto AI Weather Team</p>
        """
        
        return send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body
        )
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return False

def send_tier_upgrade_notification(user, tier):
    """
    Send notification about tier upgrade.
    
    Args:
        user: User object
        tier: New tier level
    """
    try:
        subject = "Your Toronto AI Weather account has been upgraded"
        
        # Plain text email
        text_body = f"""
        Hello {user.username},
        
        Your Toronto AI Weather account has been upgraded to {tier} level.
        
        You now have access to additional features and capabilities.
        
        Log in to your account to explore your new privileges.
        
        Best regards,
        The Toronto AI Weather Team
        """
        
        # HTML email
        html_body = f"""
        <p>Hello {user.username},</p>
        
        <p>Your Toronto AI Weather account has been upgraded to <strong>{tier}</strong> level.</p>
        
        <p>You now have access to additional features and capabilities.</p>
        
        <p>Log in to your account to explore your new privileges.</p>
        
        <p>Best regards,<br>
        The Toronto AI Weather Team</p>
        """
        
        return send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body
        )
    except Exception as e:
        logger.error(f"Error sending tier upgrade notification: {e}")
        return False

def send_weather_alert(user, alert):
    """
    Send weather alert notification.
    
    Args:
        user: User object
        alert: WeatherAlert object
    """
    try:
        subject = f"Weather Alert: {alert.title}"
        
        # Plain text email
        text_body = f"""
        Hello {user.username},
        
        A weather alert has been issued for one of your saved locations:
        
        Type: {alert.alert_type}
        Severity: {alert.severity}
        Title: {alert.title}
        Description: {alert.description}
        
        Start Time: {alert.start_time}
        End Time: {alert.end_time}
        
        Issued by: {alert.issuing_authority}
        
        Please take necessary precautions.
        
        Best regards,
        The Toronto AI Weather Team
        """
        
        # HTML email
        html_body = f"""
        <p>Hello {user.username},</p>
        
        <p>A weather alert has been issued for one of your saved locations:</p>
        
        <p><strong>Type:</strong> {alert.alert_type}<br>
        <strong>Severity:</strong> {alert.severity}<br>
        <strong>Title:</strong> {alert.title}<br>
        <strong>Description:</strong> {alert.description}</p>
        
        <p><strong>Start Time:</strong> {alert.start_time}<br>
        <strong>End Time:</strong> {alert.end_time}</p>
        
        <p><strong>Issued by:</strong> {alert.issuing_authority}</p>
        
        <p>Please take necessary precautions.</p>
        
        <p>Best regards,<br>
        The Toronto AI Weather Team</p>
        """
        
        return send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body
        )
    except Exception as e:
        logger.error(f"Error sending weather alert: {e}")
        return False
