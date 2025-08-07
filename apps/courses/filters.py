# apps/courses/filters.py
import django_filters
from django.db.models import Q
from .models import Course, Category

class CourseFilter(django_filters.FilterSet):
    """
    Filter set for Course model with advanced filtering options.
    """
    
    # Category filter
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True),
        field_name='category',
        to_field_name='slug'
    )
    
    # Level filter
    level = django_filters.ChoiceFilter(
        choices=Course.LEVEL_CHOICES,
        field_name='level'
    )
    
    # Price range filters
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte'
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )
    
    # Rating filter
    min_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte'
    )
    
    # Featured courses
    is_featured = django_filters.BooleanFilter(
        field_name='is_featured'
    )
    
    # Free courses
    is_free = django_filters.BooleanFilter(
        method='filter_free_courses'
    )
    
    # Duration filter (approximate)
    duration_type = django_filters.ChoiceFilter(
        choices=[
            ('short', 'Short (< 2 weeks)'),
            ('medium', 'Medium (2-8 weeks)'),
            ('long', 'Long (> 8 weeks)'),
        ],
        method='filter_by_duration'
    )
    
    # Teacher filter
    teacher = django_filters.CharFilter(
        field_name='teacher__name',
        lookup_expr='icontains'
    )
    
    # Search in tags
    tags = django_filters.CharFilter(
        method='filter_by_tags'
    )
    
    class Meta:
        model = Course
        fields = [
            'category', 'level', 'min_price', 'max_price', 
            'min_rating', 'is_featured', 'is_free', 
            'duration_type', 'teacher', 'tags'
        ]
    
    def filter_free_courses(self, queryset, name, value):
        """Filter for free courses (price = 0)"""
        if value:
            return queryset.filter(price=0)
        return queryset
    
    def filter_by_duration(self, queryset, name, value):
        """Filter courses by duration type"""
        if value == 'short':
            # Courses with "week" and number < 2, or "day"
            return queryset.filter(
                Q(duration__icontains='day') |
                Q(duration__icontains='1 week')
            )
        elif value == 'medium':
            # Courses with 2-8 weeks
            return queryset.filter(
                Q(duration__icontains='2 week') |
                Q(duration__icontains='3 week') |
                Q(duration__icontains='4 week') |
                Q(duration__icontains='5 week') |
                Q(duration__icontains='6 week') |
                Q(duration__icontains='7 week') |
                Q(duration__icontains='8 week') |
                Q(duration__icontains='month')
            )
        elif value == 'long':
            # Courses with > 8 weeks
            return queryset.filter(
                Q(duration__icontains='9 week') |
                Q(duration__icontains='10 week') |
                Q(duration__icontains='months') |
                Q(duration__icontains='year')
            )
        return queryset
    
    def filter_by_tags(self, queryset, name, value):
        """Filter courses by tags (JSON field search)"""
        if value:
            return queryset.filter(tags__icontains=value)
        return queryset