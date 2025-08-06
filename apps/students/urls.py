# ============================================================================
# apps/students/urls.py
# ============================================================================

from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.student_dashboard, name='dashboard'),
    
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<str:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('my-courses/', views.student_courses, name='student-courses'),
    path('enroll/', views.enroll_course, name='enroll-course'),
    path('course-progress/<str:course_id>/', views.course_progress, name='course-progress'),
    
    # Progress tracking
    path('update-progress/', views.update_module_progress, name='update-progress'),
    
    # Badges
    path('badges/', views.student_badges, name='student-badges'),
    
    # Activities
    path('activities/', views.student_activities, name='student-activities'),
]