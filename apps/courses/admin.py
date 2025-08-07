# ============================================================================
# apps/courses/admin.py
# ============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Category, Course, CourseModule, CourseEnrollment, ModuleProgress, CourseReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'course_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    def course_count(self, obj):
        """Display number of courses in this category"""
        count = obj.courses.filter(status='published').count()
        if count > 0:
            url = reverse('admin:courses_course_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} courses</a>', url, count)
        return '0 courses'
    
    course_count.short_description = 'Published Courses'

class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 1
    fields = ['title', 'type', 'duration', 'order', 'is_preview', 'is_active']
    ordering = ['order']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'teacher', 'category', 'level', 'price', 'status', 
        'rating', 'students_count', 'is_featured', 'published_at'
    ]
    list_filter = [
        'status', 'level', 'category', 'is_featured', 'created_at',
        'teacher__name'
    ]
    search_fields = ['title', 'description', 'teacher__name', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'rating', 'students_count', 'total_duration_minutes', 
        'created_at', 'updated_at', 'thumbnail_preview'
    ]
    inlines = [CourseModuleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'teacher')
        }),
        ('Course Details', {
            'fields': ('category', 'level', 'price', 'duration', 'tags')
        }),
        ('Media', {
            'fields': ('thumbnail', 'thumbnail_url', 'thumbnail_preview', 'video_preview'),
            'classes': ('collapse',)
        }),
        ('Learning Content', {
            'fields': ('learning_objectives', 'prerequisites'),
            'classes': ('collapse',)
        }),
        ('Status & Publishing', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('Metrics (Read-only)', {
            'fields': ('rating', 'students_count', 'total_duration_minutes'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_keywords', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Show thumbnail preview"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px;" />',
                obj.thumbnail.url
            )
        elif obj.thumbnail_url:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px;" />',
                obj.thumbnail_url
            )
        return "No thumbnail"
    
    thumbnail_preview.short_description = "Thumbnail Preview"
    
    actions = ['make_featured', 'remove_featured', 'publish_courses', 'unpublish_courses']
    
    def make_featured(self, request, queryset):
        """Mark selected courses as featured"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} courses marked as featured.')
    make_featured.short_description = "Mark selected courses as featured"
    
    def remove_featured(self, request, queryset):
        """Remove featured status from selected courses"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} courses removed from featured.')
    remove_featured.short_description = "Remove featured status"
    
    def publish_courses(self, request, queryset):
        """Publish selected courses"""
        from django.utils import timezone
        updated = 0
        for course in queryset:
            if course.status != 'published':
                course.status = 'published'
                if not course.published_at:
                    course.published_at = timezone.now()
                course.save()
                updated += 1
        self.message_user(request, f'{updated} courses published.')
    publish_courses.short_description = "Publish selected courses"
    
    def unpublish_courses(self, request, queryset):
        """Unpublish selected courses"""
        updated = queryset.exclude(status='published').count()
        queryset.update(status='draft')
        self.message_user(request, f'{updated} courses unpublished.')
    unpublish_courses.short_description = "Unpublish selected courses"

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'type', 'duration', 'order', 'is_preview', 'is_active']
    list_filter = ['type', 'is_preview', 'is_active', 'course__category']
    search_fields = ['title', 'description', 'course__title']
    ordering = ['course', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description', 'type', 'order')
        }),
        ('Content', {
            'fields': ('duration', 'video_url', 'content', 'resources')
        }),
        ('Settings', {
            'fields': ('is_preview', 'is_active')
        }),
    )

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student_name', 'course_title', 'status', 'progress_percentage', 
        'amount_paid', 'enrolled_at', 'completed_at'
    ]
    list_filter = [
        'status', 'enrolled_at', 'course__category', 'course__level',
        'certificate_issued'
    ]
    search_fields = [
        'student__name', 'student__email', 'course__title'
    ]
    readonly_fields = [
        'enrolled_at', 'progress_percentage', 'certificate_url'
    ]
    
    fieldsets = (
        ('Enrollment Details', {
            'fields': ('student', 'course', 'status', 'progress_percentage')
        }),
        ('Payment Information', {
            'fields': ('amount_paid', 'payment_method', 'payment_reference')
        }),
        ('Timeline', {
            'fields': ('enrolled_at', 'started_at', 'completed_at')
        }),
        ('Certificate', {
            'fields': ('certificate_issued', 'certificate_url'),
            'classes': ('collapse',)
        }),
    )
    
    def student_name(self, obj):
        """Display student name with link to profile"""
        url = reverse('admin:authentication_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.name)
    student_name.short_description = 'Student'
    
    def course_title(self, obj):
        """Display course title with link"""
        url = reverse('admin:courses_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_title.short_description = 'Course'
    
    actions = ['mark_completed', 'issue_certificates']
    
    def mark_completed(self, request, queryset):
        """Mark selected enrollments as completed"""
        from django.utils import timezone
        updated = 0
        for enrollment in queryset:
            if enrollment.status != 'completed':
                enrollment.status = 'completed'
                enrollment.completed_at = timezone.now()
                enrollment.progress_percentage = 100
                enrollment.save()
                updated += 1
        self.message_user(request, f'{updated} enrollments marked as completed.')
    mark_completed.short_description = "Mark selected enrollments as completed"
    
    def issue_certificates(self, request, queryset):
        """Issue certificates for completed courses"""
        updated = 0
        for enrollment in queryset:
            if enrollment.status == 'completed' and not enrollment.certificate_issued:
                enrollment.certificate_issued = True
                # Here you would generate the actual certificate URL
                enrollment.certificate_url = f"/certificates/{enrollment.id}/"
                enrollment.save()
                updated += 1
        self.message_user(request, f'{updated} certificates issued.')
    issue_certificates.short_description = "Issue certificates for selected enrollments"

@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = [
        'student_name', 'module_title', 'course_title', 'completed', 
        'score', 'time_spent', 'last_accessed'
    ]
    list_filter = [
        'completed', 'module__type', 'enrollment__course__category',
        'last_accessed'
    ]
    search_fields = [
        'enrollment__student__name', 'module__title', 
        'enrollment__course__title'
    ]
    readonly_fields = ['started_at', 'completed_at', 'last_accessed']
    
    def student_name(self, obj):
        """Display student name"""
        return obj.enrollment.student.name
    student_name.short_description = 'Student'
    
    def module_title(self, obj):
        """Display module title"""
        return obj.module.title
    module_title.short_description = 'Module'
    
    def course_title(self, obj):
        """Display course title"""
        return obj.enrollment.course.title
    course_title.short_description = 'Course'

@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = [
        'course_title', 'student_name', 'rating', 'title', 
        'is_verified_purchase', 'helpful_votes', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified_purchase', 'created_at',
        'course__category'
    ]
    search_fields = [
        'course__title', 'student__name', 'title', 'comment'
    ]
    readonly_fields = ['is_verified_purchase', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Review Details', {
            'fields': ('course', 'student', 'rating', 'title', 'comment')
        }),
        ('Metadata', {
            'fields': ('is_verified_purchase', 'helpful_votes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def course_title(self, obj):
        """Display course title with link"""
        url = reverse('admin:courses_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_title.short_description = 'Course'
    
    def student_name(self, obj):
        """Display student name with link"""
        url = reverse('admin:authentication_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.name)
    student_name.short_description = 'Student'
