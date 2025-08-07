from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Course, CourseModule, CourseEnrollment, ModuleProgress, CourseReview

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active']

class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_avatar = serializers.CharField(source='teacher.avatar_display_url', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    thumbnail_url = serializers.CharField(source='thumbnail_display_url', read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'teacher_name', 'teacher_avatar', 'category_name', 'price',
            'duration', 'level', 'thumbnail_url', 'rating', 'students_count',
            'tags', 'is_featured', 'published_at', 'is_enrolled',
            'total_duration_minutes'
        ]
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            return CourseEnrollment.objects.filter(
                student=request.user,
                course=obj,
                status__in=['enrolled', 'in_progress', 'completed']
            ).exists()
        return False


class TeacherBasicSerializer(serializers.ModelSerializer):
    avatar_url = serializers.CharField(source='avatar_display_url', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'avatar_url', 'rating', 'teacher_verified']

class CourseModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = [
            'id', 'title', 'description', 'type', 'duration', 'order',
            'is_preview', 'video_url', 'resources'
        ]

class CourseReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_avatar = serializers.CharField(source='student.avatar_display_url', read_only=True)
    
    class Meta:
        model = CourseReview
        fields = [
            'id', 'rating', 'title', 'comment', 'student_name', 'student_avatar',
            'helpful_votes', 'is_verified_purchase', 'created_at', 'updated_at'
        ]

class CourseDetailSerializer(serializers.ModelSerializer):
    teacher = TeacherBasicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    modules = CourseModuleSerializer(many=True, read_only=True)
    thumbnail_url = serializers.CharField(source='thumbnail_display_url', read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    enrollment_details = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'teacher', 'category', 'price', 'duration', 'level',
            'thumbnail_url', 'video_preview', 'rating', 'students_count',
            'tags', 'learning_objectives', 'prerequisites', 'modules',
            'is_featured', 'published_at', 'total_duration_minutes',
            'is_enrolled', 'enrollment_details', 'recent_reviews'
        ]
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            return CourseEnrollment.objects.filter(
                student=request.user,
                course=obj,
                status__in=['enrolled', 'in_progress', 'completed']
            ).exists()
        return False
    
    def get_enrollment_details(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            try:
                enrollment = CourseEnrollment.objects.get(
                    student=request.user,
                    course=obj,
                    status__in=['enrolled', 'in_progress', 'completed']
                )
                return {
                    'status': enrollment.status,
                    'progress_percentage': enrollment.progress_percentage,
                    'enrolled_at': enrollment.enrolled_at,
                    'started_at': enrollment.started_at,
                    'completed_at': enrollment.completed_at,
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.select_related('student').order_by('-created_at')[:5]
        return CourseReviewSerializer(recent_reviews, many=True).data

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'course_id', 'status', 'progress_percentage',
            'amount_paid', 'enrolled_at', 'started_at', 'completed_at',
            'certificate_issued', 'certificate_url'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        course = Course.objects.get(id=validated_data['course_id'])
        
        if CourseEnrollment.objects.filter(student=user, course=course).exists():
            raise serializers.ValidationError('Already enrolled in this course')
        
        enrollment = CourseEnrollment.objects.create(
            student=user,
            course=course,
            amount_paid=course.price,
            status='enrolled'
        )
        
        course.update_metrics()
        return enrollment

class TeacherCourseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    thumbnail_url = serializers.CharField(source='thumbnail_display_url', read_only=True)
    modules_count = serializers.IntegerField(source='modules.count', read_only=True)
    enrollments_count = serializers.IntegerField(source='enrollments.count', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'category', 'category_id', 'price', 'duration', 'level',
            'thumbnail_url', 'video_preview', 'rating', 'students_count',
            'tags', 'learning_objectives', 'prerequisites', 'status',
            'is_featured', 'published_at', 'created_at', 'updated_at',
            'modules_count', 'enrollments_count', 'total_duration_minutes'
        ]

class CourseStatsSerializer(serializers.Serializer):
    total_courses = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    average_rating = serializers.FloatField()
    categories_breakdown = serializers.DictField()
    level_breakdown = serializers.DictField()

class MarketplaceStatsSerializer(serializers.Serializer):
    featured_courses = CourseListSerializer(many=True)
    popular_categories = serializers.DictField()
    top_rated_courses = CourseListSerializer(many=True)
    recent_courses = CourseListSerializer(many=True)
