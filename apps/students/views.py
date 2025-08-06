# ============================================================================
# apps/students/views.py
# ============================================================================

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    Badge, StudentBadge, Course, CourseModule, 
    StudentCourse, StudentModuleProgress, StudentActivity
)
from .serializers import (
    BadgeSerializer, StudentBadgeSerializer, CourseSerializer,
    StudentCourseSerializer, StudentDashboardSerializer,
    EnrollCourseSerializer, ModuleProgressSerializer,
    UpdateModuleProgressSerializer, StudentActivitySerializer
)
from .utils import calculate_student_level, award_badges, log_activity

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    """Get comprehensive student dashboard data"""
    user = request.user
    
    # Ensure user is a student
    if user.role != 'student':
        return Response(
            {'error': 'Only students can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get student's enrolled courses
    enrolled_courses = StudentCourse.objects.filter(
        student=user
    ).select_related('course', 'course__teacher')[:5]
    
    # Get student's badges
    student_badges = StudentBadge.objects.filter(
        student=user
    ).select_related('badge')
    
    # Get recent activities
    recent_activities = StudentActivity.objects.filter(
        student=user
    )[:10]
    
    # Calculate progress statistics
    completed_courses_count = StudentCourse.objects.filter(
        student=user, 
        status='completed'
    ).count()
    
    enrolled_courses_count = StudentCourse.objects.filter(
        student=user,
        status__in=['enrolled', 'in_progress']
    ).count()
    
    total_study_time = StudentModuleProgress.objects.filter(
        student=user
    ).aggregate(total=Sum('time_spent'))['total'] or 0
    
    progress_data = {
        'total_points': user.total_points,
        'level': user.level,
        'completed_courses': completed_courses_count,
        'enrolled_courses': enrolled_courses_count,
        'study_time': total_study_time,
        'badges_count': student_badges.count()
    }
    
    dashboard_data = {
        'user': user,
        'progress': progress_data,
        'recent_courses': enrolled_courses,
        'badges': student_badges,
        'recent_activities': recent_activities
    }
    
    serializer = StudentDashboardSerializer(dashboard_data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_courses(request):
    """Get all courses for a student"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get query parameters
    status_filter = request.GET.get('status', None)
    
    queryset = StudentCourse.objects.filter(student=user).select_related('course', 'course__teacher')
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    serializer = StudentCourseSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_course(request):
    """Enroll student in a course"""
    user = request.user
    
    if user.role != 'student':
        return Response(
            {'error': 'Only students can enroll in courses'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = EnrollCourseSerializer(data=request.data)
    if serializer.is_valid():
        course_id = serializer.validated_data['course_id']
        course = get_object_or_404(Course, id=course_id, is_active=True)
        
        # Check if already enrolled
        if StudentCourse.objects.filter(student=user, course=course).exists():
            return Response(
                {'error': 'Already enrolled in this course'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create enrollment
        enrollment = StudentCourse.objects.create(
            student=user,
            course=course,
            status='enrolled'
        )
        
        # Update course student count
        course.students_count += 1
        course.save()
        
        # Log activity
        log_activity(
            user, 
            'course_start', 
            f'Enrolled in {course.title}',
            {'course_id': course_id},
            points=10
        )
        
        # Update user points
        user.total_points += 10
        user.level = calculate_student_level(user.total_points)
        user.save()
        
        serializer = StudentCourseSerializer(enrollment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    
    course = get_object_or_404(Course, id=course_id, is_active=True)
    enrollment = get_object_or_404(StudentCourse, student=user, course=course)
    
    # Get module progress
    module_progress = StudentModuleProgress.objects.filter(
        student=user,
        module__course=course
    ).select_related('module')
    
    # Get course modules
    course_serializer = CourseSerializer(course, context={'request': request})
    progress_serializer = ModuleProgressSerializer(module_progress, many=True)
    enrollment_serializer = StudentCourseSerializer(enrollment)
    
    return Response({
        'course': course_serializer.data,
        'enrollment': enrollment_serializer.data,
        'module_progress': progress_serializer.data
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
    
    serializer = UpdateModuleProgressSerializer(data=request.data)
    if serializer.is_valid():
        module_id = serializer.validated_data['module_id']
        completed = serializer.validated_data['completed']
        score = serializer.validated_data.get('score')
        time_spent = serializer.validated_data['time_spent']
        
        module = get_object_or_404(CourseModule, id=module_id, is_active=True)
        
        # Check if student is enrolled in the course
        if not StudentCourse.objects.filter(student=user, course=module.course).exists():
            return Response(
                {'error': 'Not enrolled in this course'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update or create progress
        progress, created = StudentModuleProgress.objects.get_or_create(
            student=user,
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
            progress.score = score
            progress.time_spent += time_spent
            progress.last_accessed = timezone.now()
            
            if completed and not was_completed:
                progress.completed_at = timezone.now()
        else:
            if completed:
                progress.completed_at = timezone.now()
        
        progress.save()
        
        # Award points for completion
        if completed and (created or not progress.completed):
            points = 20 if module.type == 'quiz' else 10
            user.total_points += points
            user.level = calculate_student_level(user.total_points)
            user.save()
            
            # Log activity
            log_activity(
                user,
                'module_complete',
                f'Completed {module.title}',
                {'module_id': module_id, 'course_id': str(module.course.id)},
                points
            )
        
        # Check if course is completed
        course_modules_count = CourseModule.objects.filter(course=module.course, is_active=True).count()
        completed_modules_count = StudentModuleProgress.objects.filter(
            student=user,
            module__course=module.course,
            completed=True
        ).count()
        
        # Update course progress
        enrollment = StudentCourse.objects.get(student=user, course=module.course)
        enrollment.progress_percentage = (completed_modules_count / course_modules_count) * 100
        
        if enrollment.progress_percentage >= 100 and enrollment.status != 'completed':
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
            
            # Award course completion points
            user.total_points += 100
            user.level = calculate_student_level(user.total_points)
            user.save()
            
            # Log activity
            log_activity(
                user,
                'course_complete',
                f'Completed {module.course.title}',
                {'course_id': str(module.course.id)},
                100
            )
        
        enrollment.save()
        
        # Check for new badges
        award_badges(user)
        
        serializer = ModuleProgressSerializer(progress)
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    ).select_related('badge')
    
    serializer = StudentBadgeSerializer(student_badges, many=True)
    return Response(serializer.data)

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
    
    activities = StudentActivity.objects.filter(student=user)[:20]
    serializer = StudentActivitySerializer(activities, many=True)
    return Response(serializer.data)

class CourseListView(generics.ListAPIView):
    """List all available courses"""
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by level
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)
        
        # Search by title or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.select_related('teacher')

class CourseDetailView(generics.RetrieveAPIView):
    """Get detailed course information"""
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]