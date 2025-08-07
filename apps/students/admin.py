# ============================================================================
# apps/students/admin.py
# ============================================================================

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Badge, StudentBadge, StudentActivity
)

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_id', 'icon', 'points_required', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'badge_id', 'description']
    readonly_fields = ['created_at']

@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'badge_name', 'badge_icon', 'earned_at']
    list_filter = ['earned_at', 'badge__name']
    search_fields = ['student__name', 'student__email', 'badge__name']
    readonly_fields = ['earned_at']
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student'
    
    def badge_name(self, obj):
        return obj.badge.name
    badge_name.short_description = 'Badge'
    
    def badge_icon(self, obj):
        return obj.badge.icon
    badge_icon.short_description = 'Icon'

# REMOVED: StudentModuleProgressAdmin - module progress is now managed 
# through the ModuleProgress model in the courses app

@admin.register(StudentActivity)
class StudentActivityAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'activity_type', 'description', 'points_earned', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['student__name', 'student__email', 'description']
    readonly_fields = ['timestamp']
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student'
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing