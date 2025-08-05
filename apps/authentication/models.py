
# ============================================================================
# apps/authentication/models.py
# ============================================================================

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator
from .managers import UserManager
import secrets
import string

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        error_messages={
            'unique': 'A user with this email already exists.',
        }
    )
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    avatar = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=False)  # Requires email verification
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Student specific fields
    enrolled_courses = models.JSONField(default=list, blank=True)
    completed_courses = models.JSONField(default=list, blank=True)
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # Teacher specific fields
    courses = models.JSONField(default=list, blank=True)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rating = models.FloatField(default=0.0)
    specializations = models.JSONField(default=list, blank=True)
    teacher_verified = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def save(self, *args, **kwargs):
        # Generate avatar URL if not provided
        if not self.avatar:
            self.avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={self.email}"
        
        # Set staff status for admin role
        if self.role == 'admin':
            self.is_staff = True
        
        super().save(*args, **kwargs)

class OTPVerification(models.Model):
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=[
        ('registration', 'Registration'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
    ])
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'otp_verifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.email} - {self.purpose}"
    
    @classmethod
    def generate_otp(cls):
        """Generate a random 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < 3

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'newsletter_subscriptions'
    
    def __str__(self):
        return self.email

class Waitlist(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    interest = models.CharField(max_length=100, blank=True)
    joined_at = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'waitlist'
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.name} - {self.email}"