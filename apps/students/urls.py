# apps/students/urls.py
# Updated to focus on student-specific features only

from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student Dashboard
    path('dashboard/', views.student_dashboard, name='dashboard'),
    
    # Student's enrolled courses (different from marketplace courses)
    path('my-courses/', views.student_courses, name='student-courses'),
    path('course-progress/<int:course_id>/', views.course_progress, name='course-progress'),
    
    # Progress tracking
    path('update-progress/', views.update_module_progress, name='update-progress'),
    
    # Student achievements
    path('badges/', views.student_badges, name='student-badges'),
    
    # Student activities
    path('activities/', views.student_activities, name='student-activities'),
]