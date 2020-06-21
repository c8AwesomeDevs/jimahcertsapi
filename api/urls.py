from rest_framework import routers
from django.urls import path,include
#from rest_framework_simplejwt import views as jwt_views
#from .views import *

#model_views
from api.views import CertificateViewSet,extract_data
router = routers.DefaultRouter()
router.register(r'certificates',CertificateViewSet)


urlpatterns = [
    path('',include(router.urls)),
    path('extract_data',extract_data),
]
