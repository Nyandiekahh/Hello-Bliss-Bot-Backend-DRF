# apps/students/utils.py
import math
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models

# Import existing students models only
from .models import Badge, StudentBadge, StudentActivity

# Import courses app models for course-related functionality
from apps.courses.models import CourseEnrollment, ModuleProgress

User = get_user_model()

def calculate_student_level(total_points):
    """Calculate student level based on total points"""
    if total_points < 100:
        return 1
    elif total_points < 300:
        return 2
    elif total_points < 600:
        return 3
    elif total_points < 1000:
        return 4
    elif total_points < 1500:
        return 5
    elif total_points < 2100:
        return 6
    elif total_points < 2800:
        return 7
    elif total_points < 3600:
        return 8
    elif total_points < 4500:
        return 9
    else:
        # Level 10+ uses exponential scaling
        return min(100, int(10 + math.log10(total_points / 4500)))

def log_activity(student, activity_type, description, metadata=None, points=0):
    """Log student activity and award points"""
    if metadata is None:
        metadata = {}
    
    activity = StudentActivity.objects.create(
        student=student,
        activity_type=activity_type,
        description=description,
        metadata=metadata,
        points_earned=points
    )
    
    return activity

def award_badges(student):
    """Check and award new badges to student"""
    badges_awarded = []
    
    # Get student stats using courses app models
    total_points = student.total_points
    completed_courses = CourseEnrollment.objects.filter(
        student=student, 
        status='completed'
    ).count()
    
    completed_modules = ModuleProgress.objects.filter(
        enrollment__student=student,
        completed=True
    ).count()
    
    simulation_activities = StudentActivity.objects.filter(
        student=student,
        activity_type='simulation_run'
    ).count()
    
    # Define badge criteria
    badge_criteria = [
        {
            'badge_id': 'first_circuit',
            'name': 'Circuit Builder',
            'description': 'Built your first circuit in the simulator',
            'icon': '⚡',
            'condition': lambda: simulation_activities >= 1 and StudentActivity.objects.filter(
                student=student,
                activity_type='simulation_run',
                metadata__simulation_type='circuit'
            ).exists()
        },
        {
            'badge_id': 'ros_rookie',
            'name': 'ROS Rookie',
            'description': 'Completed your first ROS simulation',
            'icon': '🤖',
            'condition': lambda: simulation_activities >= 1 and StudentActivity.objects.filter(
                student=student,
                activity_type='simulation_run',
                metadata__simulation_type='ros'
            ).exists()
        },
        {
            'badge_id': 'code_master',
            'name': 'Code Master',
            'description': 'Wrote 100 lines of robot control code',
            'icon': '💻',
            'condition': lambda: StudentActivity.objects.filter(
                student=student,
                metadata__lines_of_code__gte=100
            ).exists()
        },
        {
            'badge_id': 'first_course',
            'name': 'Learning Starter',
            'description': 'Completed your first course',
            'icon': '🎓',
            'condition': lambda: completed_courses >= 1
        },
        {
            'badge_id': 'dedicated_learner',
            'name': 'Dedicated Learner',
            'description': 'Completed 5 courses',
            'icon': '📚',
            'condition': lambda: completed_courses >= 5
        },
        {
            'badge_id': 'points_collector',
            'name': 'Points Collector',
            'description': 'Earned 1000 points',
            'icon': '🏆',
            'condition': lambda: total_points >= 1000
        },
        {
            'badge_id': 'module_master',
            'name': 'Module Master',
            'description': 'Completed 50 modules',
            'icon': '⭐',
            'condition': lambda: completed_modules >= 50
        },
        {
            'badge_id': 'simulation_expert',
            'name': 'Simulation Expert',
            'description': 'Ran 25 simulations',
            'icon': '🔬',
            'condition': lambda: simulation_activities >= 25
        },
        {
            'badge_id': 'level_up',
            'name': 'Level Up',
            'description': 'Reached level 5',
            'icon': '🚀',
            'condition': lambda: student.level >= 5
        },
        {
            'badge_id': 'high_achiever',
            'name': 'High Achiever',
            'description': 'Reached level 10',
            'icon': '👑',
            'condition': lambda: student.level >= 10
        }
    ]
    
    for badge_data in badge_criteria:
        try:
            # Check if student already has this badge
            if StudentBadge.objects.filter(
                student=student, 
                badge__badge_id=badge_data['badge_id']
            ).exists():
                continue
            
            # Check if condition is met
            if badge_data['condition']():
                # Get or create the badge
                badge, created = Badge.objects.get_or_create(
                    badge_id=badge_data['badge_id'],
                    defaults={
                        'name': badge_data['name'],
                        'description': badge_data['description'],
                        'icon': badge_data['icon']
                    }
                )
                
                # Award badge to student
                student_badge = StudentBadge.objects.create(
                    student=student,
                    badge=badge
                )
                
                badges_awarded.append(student_badge)
                
                # Log badge earning activity
                log_activity(
                    student,
                    'badge_earned',
                    f'Earned {badge.name} badge',
                    {'badge_id': badge.badge_id},
                    50  # 50 points for earning a badge
                )
                
                # Award points for badge
                student.total_points += 50
                student.level = calculate_student_level(student.total_points)
                student.save()
                
        except Exception as e:
            # Log error but continue processing other badges
            print(f"Error awarding badge {badge_data['badge_id']}: {str(e)}")
            continue
    
    return badges_awarded

def create_sample_data():
    """Create sample badges for development"""
    
    # Create sample badges
    sample_badges = [
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
        }
    ]
    
    for badge_data in sample_badges:
        Badge.objects.get_or_create(
            badge_id=badge_data['badge_id'],
            defaults=badge_data
        )
    
    print("Sample badges created successfully!")

def get_student_stats(student):
    """Get comprehensive student statistics"""
    
    # Basic stats using courses app models
    enrollments = CourseEnrollment.objects.filter(student=student)
    total_courses = enrollments.count()
    completed_courses = enrollments.filter(status='completed').count()
    in_progress_courses = enrollments.filter(status='in_progress').count()
    
    # Module stats
    module_progress_qs = ModuleProgress.objects.filter(enrollment__student=student)
    total_modules = module_progress_qs.count()
    completed_modules = module_progress_qs.filter(completed=True).count()
    
    # Time stats
    total_study_time = module_progress_qs.aggregate(
        total=models.Sum('time_spent')
    )['total'] or 0
    
    # Activity stats
    total_activities = StudentActivity.objects.filter(student=student).count()
    simulation_runs = StudentActivity.objects.filter(
        student=student,
        activity_type='simulation_run'
    ).count()
    
    # Badge stats
    total_badges = StudentBadge.objects.filter(student=student).count()
    
    # Recent activity
    recent_login = StudentActivity.objects.filter(
        student=student,
        activity_type='login'
    ).order_by('-timestamp').first()
    
    return {
        'total_points': student.total_points,
        'level': student.level,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'in_progress_courses': in_progress_courses,
        'total_modules': total_modules,
        'completed_modules': completed_modules,
        'total_study_time': total_study_time,
        'total_activities': total_activities,
        'simulation_runs': simulation_runs,
        'total_badges': total_badges,
        'last_login': recent_login.timestamp if recent_login else None,
        'completion_rate': (completed_courses / total_courses * 100) if total_courses > 0 else 0,
        'module_completion_rate': (completed_modules / total_modules * 100) if total_modules > 0 else 0
    }