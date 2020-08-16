""" 
Application Module for URL's.
TODO: (Details)
"""
from rest_framework import routers
from django.urls import path,include

#class based-views
from api.views.class_based_views import CertificateViewSet,TagConfigurationTemplateViewSet,UserActivitiesViewSet,ManualLogTemplateViewSet

#function based-views
from api.views.function_based_views import get_home,get_user_groups, \
	extract_data,view_data,save_edited_data,view_pdf, \
    upload_certificate_data,upload_manual_data,test_pi_connection, \
    preview_configuration_api,extract_manual_log_template

router = routers.DefaultRouter()
router.register(r'certificates',CertificateViewSet)
router.register(r'activitylogs',UserActivitiesViewSet)
router.register(r'tagconfigurationtemplates',TagConfigurationTemplateViewSet)
router.register(r'manuallogtemplates',ManualLogTemplateViewSet)

urlpatterns = [
    path('',include(router.urls)),
	path('home',get_home),    
	path('get_user_groups',get_user_groups),
    path('extract_data',extract_data),
    path('view_data',view_data),
    path('save_edited_data',save_edited_data),
    path('upload/certificate',upload_certificate_data),
    path('upload/manualogs',upload_manual_data),
    path('test_pi_connection',test_pi_connection),
    path('view_pdf',view_pdf),
    path('preview_configuration_api',preview_configuration_api),
    path('extract_manual_log_template',extract_manual_log_template)
]
