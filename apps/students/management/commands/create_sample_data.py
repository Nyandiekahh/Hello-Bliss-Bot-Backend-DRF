# ============================================================================
# apps/students/management/commands/create_sample_data.py
# ============================================================================

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.students.models import Badge, Course, CourseModule, StudentCourse, StudentBadge
from apps.students.utils import log_activity

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for students app'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample badges
        self.create_badges()
        
        # Create sample teacher
        teacher = self.create_teacher()
        
        # Create sample courses
        courses = self.create_courses(teacher)
        
        # Create sample student
        student = self.create_student()
        
        # Enroll student in courses
        self.enroll_student(student, courses)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
    
    def create_badges(self):
        badges_data = [
            {
                'badge_id': 'first_circuit',
                'name': 'Circuit Builder',
                'description': 'Built your first circuit in the simulator',
                'icon': '⚡'
            },
            {
                'badge_id': 'ros_rookie',
                'name': 'ROS Rookie',
                'description': 'Completed your first ROS simulation',
                'icon': '🤖'
            },
            {
                'badge_id': 'code_master',
                'name': 'Code Master',
                'description': 'Wrote 100 lines of robot control code',
                'icon': '💻'
            },
            {
                'badge_id': 'first_course',
                'name': 'Learning Starter',
                'description': 'Completed your first course',
                'icon': '🎓'
            },
            {
                'badge_id': 'dedicated_learner',
                'name': 'Dedicated Learner',
                'description': 'Completed 5 courses',
                'icon': '📚'
            },
            {
                'badge_id': 'points_collector',
                'name': 'Points Collector',
                'description': 'Earned 1000 points',
                'icon': '🏆'
            }
        ]
        
        for badge_data in badges_data:
            badge, created = Badge.objects.get_or_create(
                badge_id=badge_data['badge_id'],
                defaults=badge_data
            )
            if created:
                self.stdout.write(f'Created badge: {badge.name}')
    
    def create_teacher(self):
        teacher, created = User.objects.get_or_create(
            email='teacher@robolearn.com',
            defaults={
                'name': 'Dr. Sarah Johnson',
                'role': 'teacher',
                'is_active': True,
                'is_verified': True,
                'teacher_verified': True,
                'specializations': ['ROS', 'Circuit Design', 'Programming'],
                'rating': 4.8
            }
        )
        if created:
            teacher.set_password('teacher123')
            teacher.save()
            self.stdout.write(f'Created teacher: {teacher.name}')
        return teacher
    
    def create_courses(self, teacher):
        courses_data = [
            {
                'title': 'Introduction to Robotics',
                'description': 'Learn the fundamentals of robotics including sensors, actuators, and basic programming.',
                'price': 49.99,
                'duration': '4 weeks',
                'level': 'beginner',
                'category': 'programming',
                'rating': 4.8,
                'students_count': 1250,
                'tags': ['beginner', 'fundamentals', 'sensors'],
                'modules': [
                    {
                        'title': 'What is Robotics?',
                        'description': 'Introduction to the field of robotics',
                        'type': 'video',
                        'duration': 20,
                        'order': 1
                    },
                    {
                        'title': 'Basic Circuit Building',
                        'description': 'Learn to build your first circuit',
                        'type': 'simulation',
                        'duration': 45,
                        'order': 2
                    },
                    {
                        'title': 'Knowledge Check',
                        'description': 'Test your understanding',
                        'type': 'quiz',
                        'duration': 15,
                        'order': 3
                    }
                ]
            },
            {
                'title': 'Advanced ROS Programming',
                'description': 'Master Robot Operating System with advanced topics like navigation and computer vision.',
                'price': 99.99,
                'duration': '8 weeks',
                'level': 'advanced',
                'category': 'ros',
                'rating': 4.9,
                'students_count': 485,
                'tags': ['advanced', 'ROS', 'navigation', 'computer vision'],
                'modules': [
                    {
                        'title': 'ROS Architecture Deep Dive',
                        'description': 'Understanding nodes, topics, and services',
                        'type': 'video',
                        'duration': 35,
                        'order': 1
                    },
                    {
                        'title': 'Navigation Stack Setup',
                        'description': 'Configure robot navigation in simulation',
                        'type': 'simulation',
                        'duration': 60,
                        'order': 2
                    }
                ]
            },
            {
                'title': 'Circuit Design Masterclass',
                'description': 'From basic circuits to complex electronic systems for robotics applications.',
                'price': 79.99,
                'duration': '6 weeks',
                'level': 'intermediate',
                'category': 'circuits',
                'rating': 4.7,
                'students_count': 890,
                'tags': ['circuits', 'electronics', 'PCB design'],
                'modules': [
                    {
                        'title': 'Electronic Components Overview',
                        'description': 'Learn about resistors, capacitors, and more',
                        'type': 'video',
                        'duration': 25,
                        'order': 1
                    },
                    {
                        'title': 'Digital Logic Circuits',
                        'description': 'Build and test logic gates',
                        'type': 'simulation',
                        'duration': 40,
                        'order': 2
                    }
                ]
            }
        ]
        
        courses = []
        for course_data in courses_data:
            modules_data = course_data.pop('modules')
            
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                teacher=teacher,
                defaults=course_data
            )
            
            if created:
                self.stdout.write(f'Created course: {course.title}')
                
                # Create modules
                for module_data in modules_data:
                    module = CourseModule.objects.create(
                        course=course,
                        **module_data
                    )
                    self.stdout.write(f'  Created module: {module.title}')
            
            courses.append(course)
        
        return courses
    
    def create_student(self):
        student, created = User.objects.get_or_create(
            email='student@robolearn.com',
            defaults={
                'name': 'Alex Student',
                'role': 'student',
                'is_active': True,
                'is_verified': True,
                'total_points': 1250,
                'level': 5
            }
        )
        if created:
            student.set_password('student123')
            student.save()
            self.stdout.write(f'Created student: {student.name}')
            
            # Award some badges
            badges = Badge.objects.filter(
                badge_id__in=['first_circuit', 'ros_rookie', 'code_master']
            )
            for badge in badges:
                StudentBadge.objects.create(student=student, badge=badge)
                self.stdout.write(f'  Awarded badge: {badge.name}')
        
        return student
    
    def enroll_student(self, student, courses):
        for i, course in enumerate(courses):
            status = 'completed' if i == 0 else 'in_progress' if i == 1 else 'enrolled'
            progress = 100.0 if status == 'completed' else 50.0 if status == 'in_progress' else 0.0
            
            enrollment, created = StudentCourse.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'status': status,
                    'progress_percentage': progress
                }
            )
            
            if created:
                self.stdout.write(f'Enrolled {student.name} in {course.title} ({status})')
                
                # Log enrollment activity
                log_activity(
                    student,
                    'course_start',
                    f'Enrolled in {course.title}',
                    {'course_id': str(course.id)},
                    10
                )