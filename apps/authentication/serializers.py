# ============================================================================
# apps/authentication/serializers.py
# ============================================================================

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, OTPVerification, Newsletter, Waitlist

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'role', 'avatar', 'is_verified',
            'created_at', 'total_points', 'level', 'enrolled_courses',
            'completed_courses', 'courses', 'total_earnings', 'rating',
            'specializations', 'teacher_verified'
        ]
        read_only_fields = ['id', 'created_at', 'is_verified']
    
    def get_avatar(self, obj):
        """Return the appropriate avatar URL"""
        return obj.avatar_display_url

class ProfileSerializer(serializers.ModelSerializer):
    """Comprehensive profile serializer with all profile fields"""
    avatar = serializers.SerializerMethodField()
    interests = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            # Basic info
            'id', 'email', 'name', 'role', 'avatar', 'is_verified', 'created_at', 'updated_at',
            # Profile fields
            'first_name', 'last_name', 'phone', 'location', 'date_of_birth',
            'bio', 'interests', 'learning_goals',
            # Social profiles
            'github_profile', 'linkedin_profile',
            # Academic info
            'institution', 'major', 'year_of_study',
            # Notification preferences
            'email_notifications', 'push_notifications', 'weekly_progress',
            'course_updates', 'marketing',
            # Privacy settings
            'public_profile', 'show_progress', 'show_achievements',
            # Student/Teacher specific (read-only for profile)
            'total_points', 'level', 'enrolled_courses', 'completed_courses',
            'courses', 'total_earnings', 'rating', 'specializations', 'teacher_verified'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'is_verified', 'created_at', 'updated_at', 'name',
            'total_points', 'level', 'enrolled_courses', 'completed_courses',
            'courses', 'total_earnings', 'rating', 'specializations', 'teacher_verified'
        ]
    
    def get_avatar(self, obj):
        """Return the appropriate avatar URL"""
        return obj.avatar_display_url
    
    def validate_interests(self, value):
        """Validate interests field"""
        if value is not None:
            if not isinstance(value, list):
                raise serializers.ValidationError("Interests must be a list.")
            
            # Clean up interests - remove empty strings and duplicates
            cleaned_interests = []
            for interest in value:
                if isinstance(interest, str) and interest.strip():
                    cleaned_interest = interest.strip()
                    if cleaned_interest not in cleaned_interests:
                        cleaned_interests.append(cleaned_interest)
            
            if len(cleaned_interests) > 10:
                raise serializers.ValidationError("Maximum 10 interests allowed.")
            
            return cleaned_interests
        
        return []
    
    def validate_phone(self, value):
        """Basic phone validation"""
        if value and value.strip():
            # Remove all non-digit characters for length check
            digits_only = ''.join(filter(str.isdigit, value))
            if len(digits_only) < 7 or len(digits_only) > 15:
                raise serializers.ValidationError("Please enter a valid phone number.")
        return value
    
    def validate_date_of_birth(self, value):
        """Validate date of birth"""
        if value:
            from datetime import date
            today = date.today()
            if value > today:
                raise serializers.ValidationError("Date of birth cannot be in the future.")
            
            # Check if user is at least 13 years old
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 13:
                raise serializers.ValidationError("You must be at least 13 years old.")
        
        return value
    
    def validate_github_profile(self, value):
        """Validate GitHub profile URL"""
        if value and value.strip():
            value = value.strip()
            if not (value.startswith('http://') or value.startswith('https://')):
                value = 'https://' + value
            
            if 'github.com' not in value.lower():
                raise serializers.ValidationError("Please enter a valid GitHub profile URL.")
        
        return value
    
    def validate_linkedin_profile(self, value):
        """Validate LinkedIn profile URL"""
        if value and value.strip():
            value = value.strip()
            if not (value.startswith('http://') or value.startswith('https://')):
                value = 'https://' + value
            
            if 'linkedin.com' not in value.lower():
                raise serializers.ValidationError("Please enter a valid LinkedIn profile URL.")
        
        return value
    
    def update(self, instance, validated_data):
        """Update user profile with proper field handling"""
        
        # Handle interests separately to ensure proper JSON storage
        interests = validated_data.get('interests')
        if interests is not None:
            instance.interests = interests
        
        # Update all other fields
        for attr, value in validated_data.items():
            if attr != 'interests':  # Already handled above
                setattr(instance, attr, value)
        
        # Let the model's save() method handle name generation automatically
        instance.save()
        return instance

class BasicProfileSerializer(serializers.ModelSerializer):
    """Basic profile info for profile updates during registration"""
    interests = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'location', 'date_of_birth',
            'institution', 'major', 'year_of_study', 'bio', 'interests'
        ]
    
    def validate_interests(self, value):
        if value and not isinstance(value, list):
            raise serializers.ValidationError("Interests must be a list.")
        return value

class NotificationPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences only"""
    
    class Meta:
        model = User
        fields = [
            'email_notifications', 'push_notifications', 'weekly_progress',
            'course_updates', 'marketing'
        ]

class PrivacySettingsSerializer(serializers.ModelSerializer):
    """Serializer for privacy settings only"""
    
    class Meta:
        model = User
        fields = [
            'public_profile', 'show_progress', 'show_achievements'
        ]

class AvatarUploadSerializer(serializers.ModelSerializer):
    """Serializer for avatar file uploads"""
    avatar = serializers.ImageField(required=True)
    
    class Meta:
        model = User
        fields = ['avatar']
    
    def validate_avatar(self, value):
        """Validate uploaded avatar file"""
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("File size must be less than 5MB.")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("File must be a valid image (JPEG, PNG, GIF, or WebP).")
        
        return value

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    # Optional profile fields during registration
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    institution = serializers.CharField(required=False, allow_blank=True)
    major = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'name', 'email', 'password', 'password_confirm', 'role',
            'first_name', 'last_name', 'phone', 'location', 'institution', 'major'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_verified:
                raise serializers.ValidationError('Please verify your email before logging in.')
            if not user.is_active:
                raise serializers.ValidationError('Account is deactivated.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    purpose = serializers.CharField()

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField()

class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ['email']

class WaitlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waitlist
        fields = ['email', 'name', 'interest']

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    purpose = serializers.CharField(default='password_reset')
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs

class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)