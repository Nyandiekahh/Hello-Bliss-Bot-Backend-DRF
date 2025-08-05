
# ============================================================================
# apps/authentication/views.py
# ============================================================================

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, OTPVerification, Newsletter, Waitlist
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    OTPVerificationSerializer, ResendOTPSerializer,
    NewsletterSerializer, WaitlistSerializer
)
from .utils import generate_and_send_otp, send_welcome_email

from django.contrib.auth.hashers import make_password
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user and send OTP for verification"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate and send OTP
        otp_verification = generate_and_send_otp(user.email, 'registration')
        if otp_verification:
            return Response({
                'message': 'Registration successful. Please check your email for verification code.',
                'email': user.email,
                'requires_verification': True
            }, status=status.HTTP_201_CREATED)
        else:
            # If OTP sending fails, delete the user
            user.delete()
            return Response({
                'error': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP and activate user account"""
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        purpose = serializer.validated_data['purpose']
        
        try:
            otp_verification = OTPVerification.objects.get(
                email=email,
                otp_code=otp_code,
                purpose=purpose,
                is_used=False
            )
            
            if not otp_verification.is_valid():
                otp_verification.attempts += 1
                otp_verification.save()
                
                if otp_verification.attempts >= 3:
                    otp_verification.is_used = True
                    otp_verification.save()
                    return Response({
                        'error': 'Too many invalid attempts. Please request a new OTP.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'error': 'Invalid or expired OTP code.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used
            otp_verification.is_used = True
            otp_verification.save()
            
            if purpose == 'registration':
                # Activate user account
                try:
                    user = User.objects.get(email=email)
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                    
                    # Send welcome email
                    send_welcome_email(user)
                    
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    
                    return Response({
                        'message': 'Email verified successfully!',
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'access': str(refresh.access_token),
                            'refresh': str(refresh)
                        }
                    }, status=status.HTTP_200_OK)
                
                except User.DoesNotExist:
                    return Response({
                        'error': 'User not found.'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'message': 'OTP verified successfully!'
            }, status=status.HTTP_200_OK)
            
        except OTPVerification.DoesNotExist:
            return Response({
                'error': 'Invalid OTP code.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """Resend OTP to user email"""
    serializer = ResendOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']
        
        # Check if user exists (for registration purpose)
        if purpose == 'registration':
            try:
                user = User.objects.get(email=email)
                if user.is_verified:
                    return Response({
                        'error': 'Account is already verified.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate and send new OTP
        otp_verification = generate_and_send_otp(email, purpose)
        if otp_verification:
            return Response({
                'message': 'New verification code sent to your email.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user and return JWT tokens"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful!',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user by blacklisting refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout successful!'
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({
            'error': 'Invalid token.'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully!',
            'user': serializer.data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Newsletter and Waitlist Views
class NewsletterSubscribeView(generics.CreateAPIView):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            newsletter, created = Newsletter.objects.get_or_create(email=email)
            
            if created:
                return Response({
                    'message': 'Successfully subscribed to newsletter!'
                }, status=status.HTTP_201_CREATED)
            else:
                newsletter.is_active = True
                newsletter.save()
                return Response({
                    'message': 'Newsletter subscription reactivated!'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WaitlistJoinView(generics.CreateAPIView):
    queryset = Waitlist.objects.all()
    serializer_class = WaitlistSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            waitlist_entry, created = Waitlist.objects.get_or_create(
                email=email,
                defaults=serializer.validated_data
            )
            
            if created:
                return Response({
                    'message': 'Successfully joined the waitlist!'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'message': 'You are already on the waitlist!'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Initiate password reset by sending OTP to email"""
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        if not user.is_active:
            return Response({
                'error': 'Account is not active. Please contact support.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate and send OTP for password reset
        otp_verification = generate_and_send_otp(email, 'password_reset')
        if otp_verification:
            return Response({
                'message': 'Password reset code sent to your email.',
                'email': email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to send password reset email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        # For security, don't reveal if email exists or not
        return Response({
            'message': 'If this email exists, you will receive a password reset code.'
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using OTP verification"""
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        purpose = serializer.validated_data['purpose']
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not new_password or not confirm_password:
            return Response({
                'error': 'New password and confirmation are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'error': 'Passwords do not match.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters long.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if purpose != 'password_reset':
            return Response({
                'error': 'Invalid purpose for password reset.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            otp_verification = OTPVerification.objects.get(
                email=email,
                otp_code=otp_code,
                purpose=purpose,
                is_used=False
            )
            
            if not otp_verification.is_valid():
                otp_verification.attempts += 1
                otp_verification.save()
                
                if otp_verification.attempts >= 3:
                    otp_verification.is_used = True
                    otp_verification.save()
                    return Response({
                        'error': 'Too many invalid attempts. Please request a new reset code.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'error': 'Invalid or expired reset code.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used
            otp_verification.is_used = True
            otp_verification.save()
            
            # Reset user password
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'message': 'Password reset successfully! You can now login with your new password.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except OTPVerification.DoesNotExist:
            return Response({
                'error': 'Invalid reset code.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for authenticated user"""
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return Response({
            'error': 'Current password, new password, and confirmation are required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({
            'error': 'New passwords do not match.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    if not user.check_password(current_password):
        return Response({
            'error': 'Current password is incorrect.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': 'Password changed successfully!'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_email_change(request):
    """Request email change with OTP verification"""
    new_email = request.data.get('new_email')
    
    if not new_email:
        return Response({
            'error': 'New email is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=new_email).exists():
        return Response({
            'error': 'This email is already in use.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate and send OTP to new email
    otp_verification = generate_and_send_otp(new_email, 'email_change')
    if otp_verification:
        # Store the user id and old email in the OTP record for verification
        # We'll use a custom field or modify the model to track this
        return Response({
            'message': 'Verification code sent to your new email address.',
            'new_email': new_email
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Failed to send verification email. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email_change(request):
    """Verify email change using OTP"""
    new_email = request.data.get('new_email')
    otp_code = request.data.get('otp_code')
    
    if not all([new_email, otp_code]):
        return Response({
            'error': 'New email and OTP code are required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        otp_verification = OTPVerification.objects.get(
            email=new_email,
            otp_code=otp_code,
            purpose='email_change',
            is_used=False
        )
        
        if not otp_verification.is_valid():
            return Response({
                'error': 'Invalid or expired verification code.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark OTP as used
        otp_verification.is_used = True
        otp_verification.save()
        
        # Update user email
        user = request.user
        old_email = user.email
        user.email = new_email
        user.save()
        
        return Response({
            'message': 'Email updated successfully!',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
        
    except OTPVerification.DoesNotExist:
        return Response({
            'error': 'Invalid verification code.'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """Delete user account (requires password confirmation)"""
    password = request.data.get('password')
    confirmation = request.data.get('confirmation')
    
    if not password:
        return Response({
            'error': 'Password is required to delete account.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if confirmation != 'DELETE':
        return Response({
            'error': 'Please type "DELETE" to confirm account deletion.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    if not user.check_password(password):
        return Response({
            'error': 'Incorrect password.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Soft delete or hard delete based on your preference
    user.is_active = False
    user.email = f"deleted_{user.id}_{user.email}"  # Prevent email conflicts
    user.save()
    
    return Response({
        'message': 'Account deleted successfully.'
    }, status=status.HTTP_200_OK)