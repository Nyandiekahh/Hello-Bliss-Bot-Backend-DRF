# ============================================================================
# apps/courses/management/commands/create_sample_courses.py
# ============================================================================

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.courses.models import Category, Course, CourseModule
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample courses for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of courses to create'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        # Create categories if they don't exist
        categories_data = [
            {'name': 'Electronics', 'slug': 'circuits', 'icon': 'Cpu'},
            {'name': 'Programming', 'slug': 'programming', 'icon': 'Monitor'},
            {'name': 'ROS', 'slug': 'ros', 'icon': 'Bot'},
            {'name': 'Mechanics', 'slug': 'mechanics', 'icon': 'Zap'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories.append(category)
            if created:
                self.stdout.write(f"Created category: {category.name}")
        
        # Get or create a teacher
        teacher, created = User.objects.get_or_create(
            email='teacher@example.com',
            defaults={
                'name': 'Dr. Sarah Johnson',
                'role': 'teacher',
                'is_active': True,
                'teacher_verified': True
            }
        )
        if created:
            teacher.set_password('password123')
            teacher.save()
            self.stdout.write(f"Created teacher: {teacher.name}")
        
        # Sample course data
        course_templates = [
            {
                'title': 'Introduction to Robotics',
                'description': 'Learn the fundamentals of robotics including sensors, actuators, and basic programming.',
                'level': 'beginner',
                'price': 49.99,
                'duration': '4 weeks',
                'tags': ['beginner', 'fundamentals', 'sensors']
            },
            {
                'title': 'Advanced ROS Programming',
                'description': 'Master Robot Operating System with advanced topics like navigation and computer vision.',
                'level': 'advanced',
                'price': 99.99,
                'duration': '8 weeks',
                'tags': ['advanced', 'ROS', 'navigation', 'computer vision']
            },
            {
                'title': 'Circuit Design Masterclass',
                'description': 'From basic circuits to complex electronic systems for robotics applications.',
                'level': 'intermediate',
                'price': 79.99,
                'duration': '6 weeks',
                'tags': ['circuits', 'electronics', 'PCB design']
            },
            {
                'title': 'Python for Robotics',
                'description': 'Learn Python programming specifically for robotics applications.',
                'level': 'beginner',
                'price': 39.99,
                'duration': '3 weeks',
                'tags': ['python', 'programming', 'beginner']
            },
            {
                'title': 'Mechanical Design for Robots',
                'description': 'Design and build mechanical components for robotic systems.',
                'level': 'intermediate',
                'price': 89.99,
                'duration': '5 weeks',
                'tags': ['mechanical', 'design', 'CAD']
            },
        ]
        
        created_courses = 0
        for i in range(count):
            template = course_templates[i % len(course_templates)]
            
            # Create course
            course = Course.objects.create(
                title=f"{template['title']} {i+1}",
                description=template['description'],
                short_description=template['description'][:200],
                teacher=teacher,
                category=random.choice(categories),
                level=template['level'],
                price=template['price'],
                duration=template['duration'],
                tags=template['tags'],
                status='published',
                rating=round(random.uniform(3.5, 5.0), 1),
                students_count=random.randint(50, 1500)
            )
            
            # Create modules for each course
            module_types = ['video', 'simulation', 'quiz', 'assignment']
            for j in range(random.randint(3, 8)):
                CourseModule.objects.create(
                    course=course,
                    title=f"Module {j+1}: {template['title']} Basics",
                    description=f"Learn about {template['title']} in this module",
                    type=random.choice(module_types),
                    duration=random.randint(15, 90),
                    order=j + 1
                )
            
            created_courses += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_courses} courses')
        )