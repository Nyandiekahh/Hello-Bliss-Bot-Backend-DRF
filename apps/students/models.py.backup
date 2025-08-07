# ============================================================================
# apps/students/models.py
# ============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Badge(models.Model):
    """Badge model for student achievements"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🏆')  # Emoji or icon identifier
    badge_id = models.CharField(max_length=50, unique=True)  # Unique identifier for each badge type
    points_required = models.IntegerField(default=0)  # Points needed to earn this badge
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'badges'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class StudentBadge(models.Model):
    """Junction table for student badges"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'student_badges'
        unique_together = ['student', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.badge.name}"

class Course(models.Model):
    """Course model"""
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    CATEGORY_CHOICES = [
        ('circuits', 'Circuits'),
        ('programming', 'Programming'),
        ('ros', 'ROS'),
        ('mechanics', 'Mechanics'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_courses')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.CharField(max_length=50)  # e.g., "4 weeks"
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    thumbnail = models.URLField(blank=True, null=True)
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    students_count = models.IntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class CourseModule(models.Model):
    """Course modules/lessons"""
    MODULE_TYPES = [
        ('video', 'Video'),
        ('simulation', 'Simulation'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=MODULE_TYPES)
    duration = models.IntegerField(help_text="Duration in minutes")
    order = models.IntegerField(default=0)
    content = models.JSONField(default=dict, blank=True)  # Store module-specific content
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'course_modules'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class StudentCourse(models.Model):
    """Student course enrollment"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    progress_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    enrolled_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'student_courses'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.course.title}"

class StudentModuleProgress(models.Model):
    """Track student progress in individual modules"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='student_progress')
    completed = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)  # For quizzes/assignments
    time_spent = models.IntegerField(default=0)  # Time spent in minutes
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'student_module_progress'
        unique_together = ['student', 'module']
        ordering = ['-last_accessed']
    
    def __str__(self):
        status = "✓" if self.completed else "○"
        return f"{status} {self.student.name} - {self.module.title}"

class StudentActivity(models.Model):
    """Track student activities for analytics"""
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('course_start', 'Course Started'),
        ('module_complete', 'Module Completed'),
        ('course_complete', 'Course Completed'),
        ('badge_earned', 'Badge Earned'),
        ('simulation_run', 'Simulation Run'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=200)
    metadata = models.JSONField(default=dict, blank=True)  # Store additional activity data
    points_earned = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'student_activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.student.name} - {self.activity_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"