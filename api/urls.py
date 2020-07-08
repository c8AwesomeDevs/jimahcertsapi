from rest_framework import routers
from django.urls import path,include
#from rest_framework_simplejwt import views as jwt_views
#from .views import *

#model_views
from api.views import CertificateViewSet,UserActivitiesViewSet,extract_data,view_data,save_edited_data,upload_edited_data,test_pi_connection,view_pdf
router = routers.DefaultRouter()
router.register(r'certificates',CertificateViewSet)
router.register(r'activitylogs',UserActivitiesViewSet)


urlpatterns = [
    path('',include(router.urls)),
    path('extract_data',extract_data),
    path('view_data',view_data),
    path('save_edited_data',save_edited_data),
    path('save_edited_data',save_edited_data),
    path('upload_edited_data',upload_edited_data),
    path('test_pi_connection',test_pi_connection),
    path('view_pdf',view_pdf)
]
