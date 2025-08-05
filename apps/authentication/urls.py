
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
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
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
