# apps/students/views.py
# Fixed to work with existing students models only

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.contrib.auth import get_user_model

# Import from courses app (the primary course models)
from apps.courses.models import (
    Course, CourseModule, CourseEnrollment, ModuleProgress
)
from apps.courses.serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseEnrollmentSerializer
)

# Import only existing students app models
from .models import Badge, StudentBadge, StudentActivity

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    """Get comprehensive student dashboard data"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get student's enrolled courses (using courses app model)
    enrolled_courses = CourseEnrollment.objects.filter(
        student=user
    ).select_related('course', 'course__teacher', 'course__category')[:5]
    
    # Get student's badges
    student_badges = StudentBadge.objects.filter(
        student=user
    ).select_related('badge')
    
    # Get recent activities
    recent_activities = StudentActivity.objects.filter(
        student=user
    ).order_by('-timestamp')[:10]
    
    # Calculate progress statistics
    completed_courses_count = CourseEnrollment.objects.filter(
        student=user, 
        status='completed'
    ).count()
    
    enrolled_courses_count = CourseEnrollment.objects.filter(
        student=user,
        status__in=['enrolled', 'in_progress']
    ).count()
    
    total_study_time = ModuleProgress.objects.filter(
        enrollment__student=user
    ).aggregate(total=Sum('time_spent'))['total'] or 0
    
    progress_data = {
        'total_points': user.total_points,
        'level': user.level,
        'completed_courses': completed_courses_count,
        'enrolled_courses': enrolled_courses_count,
        'study_time': total_study_time,
        'badges_count': student_badges.count()
    }
    
    # Transform data for frontend compatibility
    dashboard_data = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'avatar': user.avatar_display_url,
            'created_at': user.created_at.isoformat(),
        },
        'progress': progress_data,
        'recent_courses': [
            {
                'id': enrollment.id,
                'course': {
                    'id': enrollment.course.id,
                    'title': enrollment.course.title,
                    'description': enrollment.course.description,
                    'teacher_name': enrollment.course.teacher.name,
                    'thumbnail': enrollment.course.thumbnail_display_url,
                    'category': enrollment.course.category.name if enrollment.course.category else None,
                    'level': enrollment.course.level,
                    'rating': enrollment.course.rating,
                    'students_count': enrollment.course.students_count,
                },
                'status': enrollment.status,
                'progress_percentage': enrollment.progress_percentage,
                'enrolled_at': enrollment.enrolled_at.isoformat(),
                'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
            }
            for enrollment in enrolled_courses
        ],
        'badges': [
            {
                'badge_id': sb.badge.badge_id,
                'name': sb.badge.name,
                'description': sb.badge.description,
                'icon': sb.badge.icon,
                'earned_at': sb.earned_at.isoformat(),
            }
            for sb in student_badges
        ],
        'recent_activities': [
            {
                'id': activity.id,
                'activity_type': activity.activity_type,
                'description': activity.description,
                'points_earned': activity.points_earned,
                'timestamp': activity.timestamp.isoformat(),
            }
            for activity in recent_activities
        ]
    }
    
    return Response(dashboard_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_courses(request):
    """Get all courses enrolled by student"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get query parameters
    status_filter = request.GET.get('status', None)
    
    queryset = CourseEnrollment.objects.filter(student=user).select_related('course', 'course__teacher', 'course__category')
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Transform for frontend
    enrollments_data = []
    for enrollment in queryset:
        enrollments_data.append({
            'id': enrollment.id,
            'course': {
                'id': enrollment.course.id,
                'title': enrollment.course.title,
                'description': enrollment.course.description,
                'teacher_id': enrollment.course.teacher.id,
                'teacher_name': enrollment.course.teacher.name,
                'teacher_avatar': enrollment.course.teacher.avatar_display_url,
                'price': enrollment.course.price,
                'duration': enrollment.course.duration,
                'level': enrollment.course.level,
                'category': enrollment.course.category.slug if enrollment.course.category else None,
                'category_name': enrollment.course.category.name if enrollment.course.category else None,
                'thumbnail': enrollment.course.thumbnail_display_url,
                'rating': enrollment.course.rating,
                'students_count': enrollment.course.students_count,
                'tags': enrollment.course.tags,
            },
            'status': enrollment.status,
            'progress_percentage': enrollment.progress_percentage,
            'enrolled_at': enrollment.enrolled_at.isoformat(),
            'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
        })
    
    return Response(enrollments_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_progress(request, course_id):
    """Get student's progress in a specific course"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    course = get_object_or_404(Course, id=course_id, status='published')
    enrollment = get_object_or_404(CourseEnrollment, student=user, course=course)
    
    # Get module progress
    module_progress = ModuleProgress.objects.filter(
        enrollment=enrollment
    ).select_related('module')
    
    return Response({
        'course': CourseDetailSerializer(course, context={'request': request}).data,
        'enrollment': CourseEnrollmentSerializer(enrollment).data,
        'module_progress': [
            {
                'module': {
                    'id': mp.module.id,
                    'title': mp.module.title,
                    'description': mp.module.description,
                    'type': mp.module.type,
                    'duration': mp.module.duration,
                    'order': mp.module.order,
                },
                'completed': mp.completed,
                'score': mp.score,
                'time_spent': mp.time_spent,
                'last_accessed': mp.last_accessed.isoformat(),
            }
            for mp in module_progress
        ]
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_module_progress(request):
    """Update student's progress on a module"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can update progress'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    module_id = request.data.get('module_id')
    completed = request.data.get('completed', False)
    score = request.data.get('score')
    time_spent = request.data.get('time_spent', 0)
    
    if not module_id:
        return Response(
            {'error': 'module_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    module = get_object_or_404(CourseModule, id=module_id, is_active=True)
    
    # Check if student is enrolled in the course
    try:
        enrollment = CourseEnrollment.objects.get(student=user, course=module.course)
    except CourseEnrollment.DoesNotExist:
        return Response(
            {'error': 'Not enrolled in this course'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update or create progress
    progress, created = ModuleProgress.objects.get_or_create(
        enrollment=enrollment,
        module=module,
        defaults={
            'completed': completed,
            'score': score,
            'time_spent': time_spent,
            'last_accessed': timezone.now()
        }
    )
    
    if not created:
        # Update existing progress
        was_completed = progress.completed
        progress.completed = completed
        if score is not None:
            progress.score = score
        progress.time_spent += time_spent
        progress.last_accessed = timezone.now()
        
        if completed and not was_completed:
            progress.completed_at = timezone.now()
    else:
        if completed:
            progress.completed_at = timezone.now()
    
    progress.save()
    
    # Update enrollment progress
    enrollment.update_progress()
    
    # Award points and log activity if module completed
    if completed and (created or not progress.completed):
        points = 20 if module.type == 'quiz' else 10
        user.total_points += points
        
        # Simple level calculation without utils
        if user.total_points < 100:
            user.level = 1
        elif user.total_points < 300:
            user.level = 2
        elif user.total_points < 600:
            user.level = 3
        elif user.total_points < 1000:
            user.level = 4
        elif user.total_points < 1500:
            user.level = 5
        else:
            user.level = min(10, 5 + (user.total_points - 1500) // 500)
        
        user.save()
        
        # Log activity
        StudentActivity.objects.create(
            student=user,
            activity_type='module_complete',
            description=f'Completed {module.title}',
            metadata={'module_id': module_id, 'course_id': str(module.course.id)},
            points_earned=points
        )
    
    return Response({
        'module': {
            'id': progress.module.id,
            'title': progress.module.title,
        },
        'completed': progress.completed,
        'score': progress.score,
        'time_spent': progress.time_spent,
        'last_accessed': progress.last_accessed.isoformat(),
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_badges(request):
    """Get all badges earned by student"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    student_badges = StudentBadge.objects.filter(
        student=user
    ).select_related('badge').order_by('-earned_at')
    
    badges_data = [
        {
            'id': sb.badge.id,
            'badge_id': sb.badge.badge_id,
            'name': sb.badge.name,
            'description': sb.badge.description,
            'icon': sb.badge.icon,
            'points_required': getattr(sb.badge, 'points_required', 0),
            'earned_at': sb.earned_at.isoformat(),
        }
        for sb in student_badges
    ]
    
    return Response(badges_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_activities(request):
    """Get student's recent activities"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    activities = StudentActivity.objects.filter(student=user).order_by('-timestamp')[:20]
    
    activities_data = [
        {
            'id': activity.id,
            'activity_type': activity.activity_type,
            'description': activity.description,
            'metadata': activity.metadata,
            'points_earned': activity.points_earned,
            'timestamp': activity.timestamp.isoformat(),
        }
        for activity in activities
    ]
    
    return Response(activities_data)