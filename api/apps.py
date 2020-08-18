"""Summary
"""
from django.apps import AppConfig


class ApiConfig(AppConfig):

    """Summary
    
    Attributes:
        name (str): Description
    """
    name = 'api'
    def ready(self):
        from .signals import log_user_logged_in_failed, log_user_logged_in_success