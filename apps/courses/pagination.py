# ============================================================================
# apps/courses/pagination.py
# ============================================================================

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CourseResultsPagination(PageNumberPagination):
    """Custom pagination for course results"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50
    
    def get_paginated_response(self, data):
        return Response({
            'pagination': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'total_count': self.page.paginator.count,
                'page_size': self.page_size,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            },
            'results': data
        })

class EnrollmentResultsPagination(PageNumberPagination):
    """Custom pagination for enrollment results"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 25