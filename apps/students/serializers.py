# ============================================================================
# apps/students/serializers.py
# ============================================================================

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Badge, StudentBadge, Course, CourseModule, 
    StudentCourse, StudentModuleProgress, StudentActivity
)

User = get_user_model()

class BadgeSerializer(serializers.ModelSerializer):
    earned_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Badge
        fields = ['badge_id', 'name', 'description', 'icon', 'earned_at']
    
    def get_earned_at(self, obj):
        # This will be populated when used with StudentBadgeSerializer
        return getattr(obj, 'earned_at', None)

class StudentBadgeSerializer(serializers.ModelSerializer):
    badge_id = serializers.CharField(source='badge.badge_id')
    name = serializers.CharField(source='badge.name')
    description = serializers.CharField(source='badge.description')
    icon = serializers.CharField(source='badge.icon')
    
    class Meta:
        model = StudentBadge
        fields = ['badge_id', 'name', 'description', 'icon', 'earned_at']

class CourseModuleSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseModule
        fields = [
            'id', 'title', 'description', 'type', 'duration', 
            'order', 'completed'
        ]
    
    def get_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = StudentModuleProgress.objects.filter(
                student=request.user,
                module=obj
            ).first()
            return progress.completed if progress else False
        return False

class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_id = serializers.CharField(source='teacher.id', read_only=True)
    modules = CourseModuleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'teacher_id', 'teacher_name',
            'price', 'duration', 'level', 'category', 'thumbnail',
            'rating', 'students_count', 'tags', 'modules'
        ]

class StudentCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    
    class Meta:
        model = StudentCourse
        fields = [
            'id', 'course', 'status', 'progress_percentage',
            'enrolled_at', 'completed_at'
        ]

class StudentProgressSerializer(serializers.Serializer):
    total_points = serializers.IntegerField()
    level = serializers.IntegerField()
    completed_courses = serializers.IntegerField()
    enrolled_courses = serializers.IntegerField()
    study_time = serializers.IntegerField()
    badges_count = serializers.IntegerField()

class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for student dashboard data"""
    user = serializers.SerializerMethodField()
    progress = StudentProgressSerializer()
    recent_courses = StudentCourseSerializer(many=True)
    badges = StudentBadgeSerializer(many=True)
    recent_activities = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        from apps.authentication.serializers import UserSerializer
        return UserSerializer(obj['user']).data
    
    def get_recent_activities(self, obj):
        return StudentActivitySerializer(obj['recent_activities'], many=True).data

class StudentActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentActivity
        fields = [
            'id', 'activity_type', 'description', 'points_earned', 'timestamp'
        ]

class EnrollCourseSerializer(serializers.Serializer):
    course_id = serializers.CharField()
    
    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value, is_active=True)
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or inactive.")

class ModuleProgressSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source='module.title', read_only=True)
    module_type = serializers.CharField(source='module.type', read_only=True)
    
    class Meta:
        model = StudentModuleProgress
        fields = [
            'id', 'module', 'module_title', 'module_type', 'completed',
            'score', 'time_spent', 'completed_at', 'last_accessed'
        ]
        read_only_fields = ['completed_at', 'last_accessed']

class UpdateModuleProgressSerializer(serializers.Serializer):
    module_id = serializers.CharField()
    completed = serializers.BooleanField(default=False)
    score = serializers.FloatField(required=False, allow_null=True)
    time_spent = serializers.IntegerField(default=0)
    
    def validate_module_id(self, value):
        try:
            module = CourseModule.objects.get(id=value, is_active=True)
            return value
        except CourseModule.DoesNotExist:
            raise serializers.ValidationError("Module not found or inactive.")