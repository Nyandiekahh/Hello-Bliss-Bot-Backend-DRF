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

# REMOVED: StudentModuleProgress model - this functionality is already covered 
# by the ModuleProgress model in apps/courses/models.py which is more comprehensive
# and properly integrated with the enrollment system.

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