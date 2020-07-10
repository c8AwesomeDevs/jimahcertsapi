""" 
Application Module for API View Pagination.
TODO: (Details)
"""

from rest_framework.pagination import PageNumberPagination

class ModifiedPagination(PageNumberPagination):
    """Modified Pagination Class
    
    Attributes:
        max_page_size (int): Maximum Page Size per request
        page_size (int): Spcified Page Size per request
        page_size_query_param (str): Page Size query parameter
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
