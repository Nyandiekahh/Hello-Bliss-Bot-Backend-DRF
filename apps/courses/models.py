# ============================================================================
# apps/courses/models.py
# ============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count

User = get_user_model()

class Category(models.Model):
    """Course categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Icon class or emoji
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'course_categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Course(models.Model):
    """Course model with comprehensive information"""
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.TextField(max_length=500, blank=True)
    
    # Teacher Information
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_courses',
        limit_choices_to={'role': 'teacher'}
    )
    
    # Course Details
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    duration = models.CharField(max_length=50)  # e.g., "4 weeks", "2 months"
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    
    # Media
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)  # For external URLs
    video_preview = models.URLField(blank=True, null=True)
    
    # Metrics (calculated fields)
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    students_count = models.IntegerField(default=0)
    total_duration_minutes = models.IntegerField(default=0)  # Total course duration
    
    # Tags and SEO
    tags = models.JSONField(default=list, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Status and Timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Learning Objectives
    learning_objectives = models.JSONField(default=list, blank=True)
    prerequisites = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['category', 'level']),
            models.Index(fields=['teacher', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def thumbnail_display_url(self):
        """Return appropriate thumbnail URL"""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.thumbnail_url:
            return self.thumbnail_url
        else:
            return f"/placeholder-course-{self.id % 5 + 1}.jpg"
    
    @property
    def teacher_name(self):
        """Get teacher's display name"""
        return self.teacher.name
    
    @property
    def category_name(self):
        """Get category name"""
        return self.category.name
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def update_metrics(self):
        """Update calculated metrics"""
        # Update students count
        self.students_count = self.enrollments.filter(status='enrolled').count()
        
        # Update rating
        avg_rating = self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        self.rating = round(avg_rating, 1) if avg_rating else 0.0
        
        # Update total duration
        total_duration = self.modules.aggregate(
            total=models.Sum('duration')
        )['total'] or 0
        self.total_duration_minutes = total_duration
        
        self.save(update_fields=['students_count', 'rating', 'total_duration_minutes'])

class CourseModule(models.Model):
    """Course modules/lessons"""
    MODULE_TYPES = [
        ('video', 'Video'),
        ('simulation', 'Simulation'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('reading', 'Reading Material'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=MODULE_TYPES)
    duration = models.IntegerField(help_text="Duration in minutes")
    order = models.IntegerField()
    
    # Content
    content = models.JSONField(default=dict, blank=True)  # Module-specific content
    video_url = models.URLField(blank=True, null=True)
    resources = models.JSONField(default=list, blank=True)  # Additional resources
    
    # Access Control
    is_preview = models.BooleanField(default=False)  # Free preview module
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_modules'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class CourseEnrollment(models.Model):
    """Student course enrollment"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('refunded', 'Refunded'),
    ]
    
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        limit_choices_to={'role': 'student'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # Status and Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    progress_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    
    # Payment Information
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    enrolled_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True, null=True)
    
    class Meta:
        db_table = 'course_enrollments'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.course.title}"
    
    def update_progress(self):
        """Calculate and update progress percentage"""
        total_modules = self.course.modules.count()
        if total_modules == 0:
            self.progress_percentage = 0
        else:
            completed_modules = self.module_progress.filter(completed=True).count()
            self.progress_percentage = (completed_modules / total_modules) * 100
        
        # Update status based on progress
        if self.progress_percentage == 100 and self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
        elif self.progress_percentage > 0 and self.status == 'enrolled':
            self.status = 'in_progress'
            if not self.started_at:
                self.started_at = timezone.now()
        
        self.save(update_fields=['progress_percentage', 'status', 'completed_at', 'started_at'])

class ModuleProgress(models.Model):
    """Track student progress in individual modules"""
    enrollment = models.ForeignKey(
        CourseEnrollment, 
        on_delete=models.CASCADE, 
        related_name='module_progress'
    )
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='student_progress')
    
    # Progress
    completed = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)  # For quizzes/assignments
    time_spent = models.IntegerField(default=0)  # Time spent in minutes
    attempts = models.IntegerField(default=0)  # Number of attempts for quizzes
    
    # Data
    progress_data = models.JSONField(default=dict, blank=True)  # Module-specific progress data
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'module_progress'
        unique_together = ['enrollment', 'module']
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['enrollment', 'completed']),
        ]
    
    def __str__(self):
        status = "✓" if self.completed else "○"
        return f"{status} {self.enrollment.student.name} - {self.module.title}"

class CourseReview(models.Model):
    """Course reviews and ratings"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='course_reviews',
        limit_choices_to={'role': 'student'}
    )
    
    # Review Content
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    
    # Metadata
    helpful_votes = models.IntegerField(default=0)
    is_verified_purchase = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_reviews'
        unique_together = ['course', 'student']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.rating}★ by {self.student.name}"
    
    def save(self, *args, **kwargs):
        # Check if this is a verified purchase
        self.is_verified_purchase = CourseEnrollment.objects.filter(
            student=self.student,
            course=self.course,
            status__in=['enrolled', 'in_progress', 'completed']
        ).exists()
        
        super().save(*args, **kwargs)
        
        # Update course rating
        self.course.update_metrics()