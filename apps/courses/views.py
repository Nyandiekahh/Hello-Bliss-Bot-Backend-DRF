# ============================================================================
# apps/courses/views.py
# ============================================================================

from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404

from .models import Category, Course, CourseEnrollment, CourseReview
from .serializers import (
    CategorySerializer, CourseListSerializer, CourseDetailSerializer,
    CourseEnrollmentSerializer, CourseReviewSerializer, TeacherCourseSerializer,
    CourseStatsSerializer, MarketplaceStatsSerializer
)
from .filters import CourseFilter
from .permissions import IsTeacherOrReadOnly, IsOwnerOrReadOnly

# ============================================================================
# Public API Views (No Authentication Required)
# ============================================================================

class CategoryListView(generics.ListAPIView):
    """List all active categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class CourseListView(generics.ListAPIView):
    """List all published courses with filtering and search"""
    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description', 'tags', 'teacher__name']
    ordering_fields = ['created_at', 'rating', 'students_count', 'price']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """Get published courses with optimized queries"""
        return Course.objects.filter(
            status='published'
        ).select_related(
            'teacher', 'category'
        ).prefetch_related(
            'enrollments'
        ).order_by('-created_at')

class CourseDetailView(generics.RetrieveAPIView):
    """Get detailed course information"""
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get published courses with all related data"""
        return Course.objects.filter(
            status='published'
        ).select_related(
            'teacher', 'category'
        ).prefetch_related(
            'modules', 'reviews__student'
        )

# ============================================================================
# Marketplace Overview
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def marketplace_overview(request):
    """Get marketplace overview data"""
    # Featured courses
    featured_courses = Course.objects.filter(
        status='published',
        is_featured=True
    ).select_related('teacher', 'category')[:6]
    
    # Popular categories (by course count)
    popular_categories = Category.objects.filter(
        is_active=True
    ).annotate(
        course_count=Count('courses', filter=Q(courses__status='published'))
    ).order_by('-course_count')[:6]
    
    # Top rated courses
    top_rated_courses = Course.objects.filter(
        status='published',
        rating__gte=4.0
    ).select_related('teacher', 'category').order_by('-rating', '-students_count')[:6]
    
    # Recent courses
    recent_courses = Course.objects.filter(
        status='published'
    ).select_related('teacher', 'category').order_by('-published_at')[:6]
    
    context = {'request': request}
    
    data = {
        'featured_courses': CourseListSerializer(featured_courses, many=True, context=context).data,
        'popular_categories': {
            cat.slug: {
                'name': cat.name,
                'course_count': cat.course_count,
                'icon': cat.icon
            } for cat in popular_categories
        },
        'top_rated_courses': CourseListSerializer(top_rated_courses, many=True, context=context).data,
        'recent_courses': CourseListSerializer(recent_courses, many=True, context=context).data,
    }
    
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def course_stats(request):
    """Get overall course statistics"""
    stats = {
        'total_courses': Course.objects.filter(status='published').count(),
        'total_students': CourseEnrollment.objects.filter(
            status__in=['enrolled', 'in_progress', 'completed']
        ).values('student').distinct().count(),
        'total_enrollments': CourseEnrollment.objects.filter(
            status__in=['enrolled', 'in_progress', 'completed']
        ).count(),
        'average_rating': Course.objects.filter(
            status='published'
        ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0,
    }
    
    # Categories breakdown
    categories_breakdown = {}
    for category in Category.objects.filter(is_active=True):
        count = Course.objects.filter(category=category, status='published').count()
        if count > 0:
            categories_breakdown[category.slug] = {
                'name': category.name,
                'count': count
            }
    
    # Level breakdown
    level_breakdown = {}
    for level_choice in Course.LEVEL_CHOICES:
        level_slug = level_choice[0]
        level_name = level_choice[1]
        count = Course.objects.filter(level=level_slug, status='published').count()
        if count > 0:
            level_breakdown[level_slug] = {
                'name': level_name,
                'count': count
            }
    
    stats['categories_breakdown'] = categories_breakdown
    stats['level_breakdown'] = level_breakdown
    
    return Response(stats)

# ============================================================================
# Student Enrollment Views
# ============================================================================

class CourseEnrollmentListView(generics.ListAPIView):
    """List student's enrolled courses"""
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get current user's enrollments"""
        if self.request.user.role != 'student':
            return CourseEnrollment.objects.none()
        
        return CourseEnrollment.objects.filter(
            student=self.request.user
        ).select_related('course__teacher', 'course__category').order_by('-enrolled_at')

class CourseEnrollmentCreateView(generics.CreateAPIView):
    """Enroll in a course"""
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Ensure only students can enroll"""
        if self.request.user.role != 'student':
            raise PermissionError("Only students can enroll in courses")
        serializer.save()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_in_course(request, course_id):
    """Enroll student in a specific course"""
    if request.user.role != 'student':
        return Response(
            {'error': 'Only students can enroll in courses'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id, status='published')
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if already enrolled
    if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
        return Response(
            {'error': 'Already enrolled in this course'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create enrollment
    enrollment = CourseEnrollment.objects.create(
        student=request.user,
        course=course,
        amount_paid=course.price,
        status='enrolled'
    )
    
    # Update course metrics
    course.update_metrics()
    
    serializer = CourseEnrollmentSerializer(enrollment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def enrollment_status(request, course_id):
    """Check if user is enrolled in a course"""
    if request.user.role != 'student':
        return Response({'enrolled': False})
    
    try:
        enrollment = CourseEnrollment.objects.get(
            student=request.user,
            course_id=course_id,
            status__in=['enrolled', 'in_progress', 'completed']
        )
        return Response({
            'enrolled': True,
            'status': enrollment.status,
            'progress_percentage': enrollment.progress_percentage,
            'enrolled_at': enrollment.enrolled_at
        })
    except CourseEnrollment.DoesNotExist:
        return Response({'enrolled': False})

# ============================================================================
# Course Reviews
# ============================================================================

class CourseReviewListCreateView(generics.ListCreateAPIView):
    """List and create course reviews"""
    serializer_class = CourseReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get reviews for a specific course"""
        course_id = self.kwargs.get('course_id')
        return CourseReview.objects.filter(
            course_id=course_id
        ).select_related('student').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create review for authenticated student"""
        if self.request.user.role != 'student':
            raise PermissionError("Only students can review courses")
        
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id, status='published')
        
        # Check if student is enrolled
        if not CourseEnrollment.objects.filter(
            student=self.request.user,
            course=course,
            status__in=['enrolled', 'in_progress', 'completed']
        ).exists():
            raise PermissionError("You must be enrolled to review this course")
        
        serializer.save(student=self.request.user, course=course)

# ============================================================================
# Teacher Views
# ============================================================================

class TeacherCourseListView(generics.ListCreateAPIView):
    """List teacher's courses and create new courses"""
    serializer_class = TeacherCourseSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrReadOnly]
    
    def get_queryset(self):
        """Get courses created by current teacher"""
        if self.request.user.role != 'teacher':
            return Course.objects.none()
        
        return Course.objects.filter(
            teacher=self.request.user
        ).select_related('category').order_by('-created_at')

class TeacherCourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete teacher's course"""
    serializer_class = TeacherCourseSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Get courses owned by current teacher"""
        if self.request.user.role != 'teacher':
            return Course.objects.none()
        
        return Course.objects.filter(teacher=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard_stats(request):
    """Get dashboard statistics for teachers"""
    if request.user.role != 'teacher':
        return Response(
            {'error': 'Only teachers can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    teacher_courses = Course.objects.filter(teacher=request.user)
    
    stats = {
        'total_courses': teacher_courses.count(),
        'published_courses': teacher_courses.filter(status='published').count(),
        'draft_courses': teacher_courses.filter(status='draft').count(),
        'total_students': CourseEnrollment.objects.filter(
            course__teacher=request.user,
            status__in=['enrolled', 'in_progress', 'completed']
        ).values('student').distinct().count(),
        'total_enrollments': CourseEnrollment.objects.filter(
            course__teacher=request.user,
            status__in=['enrolled', 'in_progress', 'completed']
        ).count(),
        'average_rating': teacher_courses.filter(
            status='published'
        ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0,
        'total_earnings': sum(
            enrollment.amount_paid for enrollment in CourseEnrollment.objects.filter(
                course__teacher=request.user,
                status__in=['enrolled', 'in_progress', 'completed']
            )
        ),
    }
    
    return Response(stats)

# ============================================================================
# Search and Filter Views
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def search_courses(request):
    """Advanced course search with filters"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    level = request.GET.get('level', '')
    min_rating = request.GET.get('min_rating', 0)
    max_price = request.GET.get('max_price', None)
    sort_by = request.GET.get('sort_by', 'created_at')
    
    # Base queryset
    courses = Course.objects.filter(status='published').select_related('teacher', 'category')
    
    # Apply search query
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(teacher__name__icontains=query)
        )
    
    # Apply filters
    if category and category != 'all':
        courses = courses.filter(category__slug=category)
    
    if level:
        courses = courses.filter(level=level)
    
    if min_rating:
        try:
            courses = courses.filter(rating__gte=float(min_rating))
        except ValueError:
            pass
    
    if max_price:
        try:
            courses = courses.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply sorting
    sort_options = {
        'created_at': '-created_at',
        'rating': '-rating',
        'students_count': '-students_count',
        'price_low': 'price',
        'price_high': '-price',
        'title': 'title'
    }
    
    if sort_by in sort_options:
        courses = courses.order_by(sort_options[sort_by])
    
    # Paginate results
    from django.core.paginator import Paginator
    paginator = Paginator(courses, 12)  # 12 courses per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {'request': request}
    serializer = CourseListSerializer(page_obj, many=True, context=context)
    
    return Response({
        'courses': serializer.data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })

# ============================================================================
# Utility Views
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def course_suggestions(request):
    """Get course suggestions based on popularity and ratings"""
    # Get popular courses (high enrollment)
    popular_courses = Course.objects.filter(
        status='published',
        students_count__gt=0
    ).select_related('teacher', 'category').order_by('-students_count')[:6]
    
    # Get trending courses (recently published with good ratings)
    from datetime import datetime, timedelta
    trending_courses = Course.objects.filter(
        status='published',
        published_at__gte=datetime.now() - timedelta(days=30),
        rating__gte=4.0
    ).select_related('teacher', 'category').order_by('-rating', '-students_count')[:6]
    
    context = {'request': request}
    
    return Response({
        'popular_courses': CourseListSerializer(popular_courses, many=True, context=context).data,
        'trending_courses': CourseListSerializer(trending_courses, many=True, context=context).data,
    })