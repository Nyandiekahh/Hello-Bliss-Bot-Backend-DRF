# apps/courses/urls.py
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # ============================================================================
    # Public API endpoints (No Authentication Required)
    # ============================================================================
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course-detail'),
    
    # Marketplace
    path('marketplace/overview/', views.marketplace_overview, name='marketplace-overview'),
    path('marketplace/stats/', views.course_stats, name='course-stats'),
    
    # Search
    path('search/', views.search_courses, name='search-courses'),
    path('courses/suggestions/', views.course_suggestions, name='course-suggestions'),
    
    # ============================================================================
    # Student endpoints (Authentication Required)
    # ============================================================================
    
    # Enrollments
    path('enrollments/', views.CourseEnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/create/', views.CourseEnrollmentCreateView.as_view(), name='enrollment-create'),
    path('courses/<int:course_id>/enroll/', views.enroll_in_course, name='enroll-course'),
    path('courses/<int:course_id>/enrollment-status/', views.enrollment_status, name='enrollment-status'),
    
    # Reviews
    path('courses/<int:course_id>/reviews/', views.CourseReviewListCreateView.as_view(), name='course-reviews'),
    
    # ============================================================================
    # Teacher endpoints (Teacher Authentication Required)
    # ============================================================================
    
    # Teacher course management
    path('teacher/courses/', views.TeacherCourseListView.as_view(), name='teacher-courses'),
    path('teacher/courses/<int:pk>/', views.TeacherCourseDetailView.as_view(), name='teacher-course-detail'),
    path('teacher/dashboard/stats/', views.teacher_dashboard_stats, name='teacher-dashboard-stats'),
]