# ============================================================================
# apps/courses/signals.py
# ============================================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CourseEnrollment, ModuleProgress, CourseReview

@receiver(post_save, sender=CourseEnrollment)
def update_course_metrics_on_enrollment(sender, instance, created, **kwargs):
    """Update course metrics when enrollment is created or updated"""
    if created:
        # Update course student count
        instance.course.update_metrics()

@receiver(post_delete, sender=CourseEnrollment)
def update_course_metrics_on_unenrollment(sender, instance, **kwargs):
    """Update course metrics when enrollment is deleted"""
    instance.course.update_metrics()

@receiver(post_save, sender=ModuleProgress)
def update_enrollment_progress(sender, instance, created, **kwargs):
    """Update enrollment progress when module progress changes"""
    if instance.completed:
        instance.enrollment.update_progress()

@receiver(post_save, sender=CourseReview)
@receiver(post_delete, sender=CourseReview)
def update_course_rating(sender, instance, **kwargs):
    """Update course rating when reviews are added or removed"""
    instance.course.update_metrics()
