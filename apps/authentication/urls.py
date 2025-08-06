# ============================================================================
# apps/authentication/urls.py
# ============================================================================

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # OTP Verification
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # Profile Management
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/basic/', views.update_basic_profile, name='update_basic_profile'),
    path('profile/notifications/', views.update_notification_preferences, name='update_notification_preferences'),
    path('profile/privacy/', views.update_privacy_settings, name='update_privacy_settings'),
    
    # Avatar Management (Updated)
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),  # For file uploads
    path('profile/avatar/url/', views.upload_avatar_url, name='upload_avatar_url'),  # For URL uploads
    path('profile/avatar/delete/', views.delete_avatar, name='delete_avatar'),
    
    # Newsletter and Waitlist
    path('newsletter/subscribe/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    path('waitlist/join/', views.WaitlistJoinView.as_view(), name='waitlist_join'),

    # Password Reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Email Change
    path('request-email-change/', views.request_email_change, name='request_email_change'),
    path('verify-email-change/', views.verify_email_change, name='verify_email_change'),
    
    # Account Management
    path('delete-account/', views.delete_account, name='delete_account'),
]