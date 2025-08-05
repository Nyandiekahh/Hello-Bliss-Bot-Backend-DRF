
# ============================================================================
# apps/authentication/admin.py
# ============================================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, OTPVerification, Newsletter, Waitlist

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'name', 'role', 'is_verified', 'is_active', 
        'total_points', 'level', 'created_at'
    ]
    list_filter = ['role', 'is_verified', 'is_active', 'created_at']
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'avatar', 'role')}),
        ('Permissions', {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Student Info', {
            'fields': ('enrolled_courses', 'completed_courses', 'total_points', 'level'),
            'classes': ('collapse',),
        }),
        ('Teacher Info', {
            'fields': ('courses', 'total_earnings', 'rating', 'specializations', 'teacher_verified'),
            'classes': ('collapse',),
        }),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'last_login']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'purpose', 'otp_code', 'created_at', 
        'expires_at', 'is_used', 'attempts', 'is_expired_status'
    ]
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'expires_at']
    
    def is_expired_status(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_status.short_description = 'Status'

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    ordering = ['-subscribed_at']
    readonly_fields = ['subscribed_at']

@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'interest', 'joined_at', 'notified']
    list_filter = ['notified', 'interest', 'joined_at']
    search_fields = ['email', 'name']
    ordering = ['-joined_at']
    readonly_fields = ['joined_at']
    
    actions = ['mark_as_notified', 'mark_as_not_notified']
    
    def mark_as_notified(self, request, queryset):
        queryset.update(notified=True)
        self.message_user(request, f'{queryset.count()} entries marked as notified.')
    mark_as_notified.short_description = 'Mark selected entries as notified'
    
    def mark_as_not_notified(self, request, queryset):
        queryset.update(notified=False)
        self.message_user(request, f'{queryset.count()} entries marked as not notified.')
    mark_as_not_notified.short_description = 'Mark selected entries as not notified'
