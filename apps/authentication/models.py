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

def user_avatar_path(instance, filename):
    """Generate upload path for user avatars"""
    return f'avatars/user_{instance.id}/{filename}'

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    
    YEAR_OF_STUDY_CHOICES = [
        ('freshman', 'Freshman'),
        ('sophomore', 'Sophomore'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('graduate', 'Graduate'),
        ('phd', 'PhD'),
    ]
    
    # Basic user fields
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        error_messages={
            'unique': 'A user with this email already exists.',
        }
    )
    # FIXED: Make name field allow blank values
    name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    
    # Updated avatar field to support both file uploads and URLs
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)  # For external URLs
    
    is_active = models.BooleanField(default=False)  # Requires email verification
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Profile fields
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    interests = models.JSONField(default=list, blank=True)
    learning_goals = models.TextField(blank=True)
    
    # Social profiles
    github_profile = models.URLField(blank=True)
    linkedin_profile = models.URLField(blank=True)
    
    # Academic information
    institution = models.CharField(max_length=255, blank=True)
    major = models.CharField(max_length=255, blank=True)
    year_of_study = models.CharField(max_length=20, choices=YEAR_OF_STUDY_CHOICES, blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    weekly_progress = models.BooleanField(default=True)
    course_updates = models.BooleanField(default=True)
    marketing = models.BooleanField(default=False)
    
    # Privacy settings
    public_profile = models.BooleanField(default=False)
    show_progress = models.BooleanField(default=True)
    show_achievements = models.BooleanField(default=True)
    
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
    
    @property
    def avatar_display_url(self):
        """Return the appropriate avatar URL for display"""
        if self.avatar:
            return self.avatar.url
        elif self.avatar_url:
            return self.avatar_url
        else:
            # Generate a fallback avatar based on name
            display_name = self.name or self.email.split('@')[0]
            initials = ''.join([word[0] for word in display_name.split()[:2]]).upper()
            return f"https://ui-avatars.com/api/?name={initials}&background=3B82F6&color=FFFFFF&size=200&font-size=0.6"
    
    def save(self, *args, **kwargs):
        # Auto-populate first_name and last_name from name if not provided
        if self.name and (not self.first_name or not self.last_name):
            name_parts = self.name.split(' ', 1)
            if not self.first_name:
                self.first_name = name_parts[0]
            if not self.last_name and len(name_parts) > 1:
                self.last_name = name_parts[1]
        
        # Auto-populate name from first_name and last_name if name is empty
        if not self.name and (self.first_name or self.last_name):
            self.name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        
        # Fallback to email username if still no name
        if not self.name:
            self.name = self.email.split('@')[0] if self.email else 'User'
        
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