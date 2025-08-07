# apps/courses/permissions.py
from rest_framework import permissions

class IsTeacherOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow teachers to create/edit courses.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for authenticated teachers
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'teacher'
        )

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner of the object
        return obj.teacher == request.user

class IsStudentOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow students to enroll/review courses.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for authenticated students
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'student'
        )