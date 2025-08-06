# ============================================================================
# apps/students/tests.py
# ============================================================================

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Badge, Course, CourseModule, StudentCourse
from .utils import calculate_student_level, award_badges

User = get_user_model()

class StudentModelsTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='test@student.com',
            name='Test Student',
            password='testpass123',
            role='student',
            is_verified=True
        )
        
        self.teacher = User.objects.create_user(
            email='test@teacher.com',
            name='Test Teacher',
            password='testpass123',
            role='teacher',
            is_verified=True
        )
    
    def test_student_level_calculation(self):
        """Test student level calculation"""
        self.assertEqual(calculate_student_level(50), 1)
        self.assertEqual(calculate_student_level(150), 2)
        self.assertEqual(calculate_student_level(500), 3)
        self.assertEqual(calculate_student_level(1200), 5)
    
    def test_badge_creation(self):
        """Test badge creation"""
        badge = Badge.objects.create(
            badge_id='test_badge',
            name='Test Badge',
            description='A test badge',
            icon='🏆'
        )
        self.assertEqual(str(badge), 'Test Badge')
    
    def test_course_creation(self):
        """Test course creation"""
        course = Course.objects.create(
            title='Test Course',
            description='A test course',
            teacher=self.teacher,
            price=29.99,
            duration='2 weeks',
            level='beginner',
            category='programming'
        )
        self.assertEqual(str(course), 'Test Course')
        self.assertEqual(course.teacher, self.teacher)

class StudentAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.student = User.objects.create_user(
            email='api@student.com',
            name='API Student',
            password='testpass123',
            role='student',
            is_verified=True,
            total_points=500,
            level=3
        )
        
        self.teacher = User.objects.create_user(
            email='api@teacher.com',
            name='API Teacher',
            password='testpass123',
            role='teacher',
            is_verified=True
        )
        
        # Create a test course
        self.course = Course.objects.create(
            title='API Test Course',
            description='A course for API testing',
            teacher=self.teacher,
            price=49.99,
            duration='3 weeks',
            level='beginner',
            category='programming'
        )
        
        # Create course modules
        self.module1 = CourseModule.objects.create(
            course=self.course,
            title='Module 1',
            description='First module',
            type='video',
            duration=30,
            order=1
        )
        
        self.module2 = CourseModule.objects.create(
            course=self.course,
            title='Module 2',
            description='Second module',
            type='quiz',
            duration=15,
            order=2
        )
    
    def test_student_dashboard_access(self):
        """Test student dashboard API access"""
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/students/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('progress', response.data)
    
    def test_course_enrollment(self):
        """Test course enrollment API"""
        self.client.force_authenticate(user=self.student)
        data = {'course_id': str(self.course.id)}
        response = self.client.post('/api/students/enroll/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if enrollment was created
        self.assertTrue(
            StudentCourse.objects.filter(
                student=self.student, 
                course=self.course
            ).exists()
        )
    
    def test_duplicate_enrollment_prevention(self):
        """Test prevention of duplicate enrollments"""
        # Create initial enrollment
        StudentCourse.objects.create(
            student=self.student,
            course=self.course,
            status='enrolled'
        )
        
        self.client.force_authenticate(user=self.student)
        data = {'course_id': str(self.course.id)}
        response = self.client.post('/api/students/enroll/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_course_list_access(self):
        """Test course list API"""
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/students/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)
    
    def test_unauthorized_access(self):
        """Test unauthorized access prevention"""
        response = self.client.get('/api/students/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_teacher_dashboard_access_denied(self):
        """Test that teachers cannot access student dashboard"""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/students/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)