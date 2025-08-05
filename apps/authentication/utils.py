

# ============================================================================
# apps/authentication/utils.py
# ============================================================================

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OTPVerification
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email, otp_code, purpose):
    """Send OTP email to user"""
    subject_map = {
        'registration': 'Verify Your RoboLearn Account',
        'password_reset': 'Reset Your RoboLearn Password',
        'email_change': 'Verify Your New Email Address',
    }
    
    message_map = {
        'registration': f"""
Welcome to RoboLearn!

Your verification code is: {otp_code}

This code will expire in 10 minutes. Please use it to verify your account.

If you didn't create an account with RoboLearn, please ignore this email.

Best regards,
The RoboLearn Team
        """,
        'password_reset': f"""
Password Reset Request

Your password reset code is: {otp_code}

This code will expire in 10 minutes. Use it to reset your password.

If you didn't request a password reset, please ignore this email.

Best regards,
The RoboLearn Team
        """,
        'email_change': f"""
Email Change Verification

Your email change verification code is: {otp_code}

This code will expire in 10 minutes.

If you didn't request an email change, please contact support immediately.

Best regards,
The RoboLearn Team
        """
    }
    
    try:
        send_mail(
            subject=subject_map.get(purpose, 'RoboLearn Verification Code'),
            message=message_map.get(purpose, f'Your verification code is: {otp_code}'),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False

def generate_and_send_otp(email, purpose):
    """Generate OTP and send email"""
    # Invalidate any existing OTPs for this email and purpose
    OTPVerification.objects.filter(
        email=email, 
        purpose=purpose, 
        is_used=False
    ).update(is_used=True)
    
    # Generate new OTP
    otp_code = OTPVerification.generate_otp()
    expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    # Create OTP record
    otp_verification = OTPVerification.objects.create(
        email=email,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=expires_at
    )
    
    # Send email
    if send_otp_email(email, otp_code, purpose):
        return otp_verification
    else:
        otp_verification.delete()
        return None

def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = "Welcome to RoboLearn - Your Robotics Journey Begins!"
    message = f"""
Hi {user.name},

Welcome to RoboLearn! 🤖

Your account has been successfully verified and you're now part of our robotics learning community.

Here's what you can do next:
- Explore our course marketplace
- Start with beginner-friendly robotics courses
- Use our interactive simulators
- Join the community discussions

Ready to start your robotics journey? Login to your dashboard and begin learning!

Best regards,
The RoboLearn Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(email, otp_code):
    """Send password reset email"""
    subject = "Reset Your RoboLearn Password"
    message = f"""
Password Reset Request

Your password reset code is: {otp_code}

This code will expire in 10 minutes. Use it to reset your password.

If you didn't request a password reset, please ignore this email and consider changing your password for security.

Best regards,
The RoboLearn Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        return False