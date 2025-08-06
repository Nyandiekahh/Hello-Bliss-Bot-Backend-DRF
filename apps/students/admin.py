# ============================================================================
# apps/students/admin.py
# ============================================================================

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Badge, StudentBadge, Course, CourseModule, 
    StudentCourse, StudentModuleProgress, StudentActivity
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

class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 1
    fields = ['title', 'type', 'duration', 'order', 'is_active']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'level', 'category', 'price', 'students_count', 'rating', 'is_active']
    list_filter = ['level', 'category', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'teacher__name']
    readonly_fields = ['students_count', 'rating', 'created_at', 'updated_at']
    inlines = [CourseModuleInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'teacher')
        }),
        ('Course Details', {
            'fields': ('price', 'duration', 'level', 'category', 'thumbnail', 'tags')
        }),
        ('Statistics', {
            'fields': ('students_count', 'rating', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'type', 'duration', 'order', 'is_active']
    list_filter = ['type', 'is_active', 'course__category']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['created_at']

@admin.register(StudentCourse)
class StudentCourseAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_title', 'status', 'progress_percentage', 'enrolled_at', 'completed_at']
    list_filter = ['status', 'enrolled_at', 'course__category', 'course__level']
    search_fields = ['student__name', 'student__email', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at']
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student'
    
    def course_title(self, obj):
        return obj.course.title
    course_title.short_description = 'Course'

@admin.register(StudentModuleProgress)
class StudentModuleProgressAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'module_title', 'completed', 'score', 'time_spent', 'last_accessed']
    list_filter = ['completed', 'module__type', 'last_accessed']
    search_fields = ['student__name', 'module__title', 'module__course__title']
    readonly_fields = ['completed_at', 'last_accessed']
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student'
    
    def module_title(self, obj):
        return obj.module.title
    module_title.short_description = 'Module'

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