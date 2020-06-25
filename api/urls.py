from rest_framework import routers
from django.urls import path,include
#from rest_framework_simplejwt import views as jwt_views
#from .views import *

#model_views
from api.views import CertificateViewSet,extract_data,save_edited_data,upload_edited_data
router = routers.DefaultRouter()
router.register(r'certificates',CertificateViewSet)


urlpatterns = [
    path('',include(router.urls)),
    path('extract_data',extract_data),
    path('save_edited_data',save_edited_data),
    path('save_edited_data',save_edited_data),
    path('upload_edited_data',upload_edited_data),
]
