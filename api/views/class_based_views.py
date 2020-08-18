""" 
Application Module for Views.
TODO: (Details)
"""


# Django Libraries
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated,BasePermission
from rest_framework_jwt.views import ObtainJSONWebToken
#Developer Libaries
from api.models import Certificate,ExtractedDataCSV,TagConfigurationTemplate,ManualLogTemplate,CoalParameters,CoalParametersSection,CoalParametersDividers,UserActivities
from api.serializers import CertificateSerializer,UserActivitiesSerializer,TagConfigurationTemplateSerializer,ManualLogTemplateSerializer,JWTSerializer
from api.pagination import ModifiedPagination


#PERMISSIONS
class IsDataValidator(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='data_validator'):
            return True
        return False


#VIEWS
# Create your views here.
class ObtainJWTView(ObtainJSONWebToken):
    serializer_class = JWTSerializer

class CertificateViewSet(viewsets.ModelViewSet):
    """API Class View for Certificates model.
    
    Attributes:
        permission_classes (Tuple): Tuple of Permission Classes.
        queryset (QuerySet): Queryset for all certificates
        serializer_class (Object): Type of Model Serializer.

    Methods:
        list(request)
            Returns an api response of the list of certificates.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = CertificateSerializer
    queryset = Certificate.objects.all()
    def list(self, request):
        """Returns an api response of the list of certificates.
        
        Args:
            request (Request): A request instance

        Returns:
            Response: An API response of the list of certificates.
        """
        queryset = Certificate.objects.all()
        serializer = CertificateSerializer(queryset, many=True)
        user = request.user
        return Response(serializer.data)

    def partial_update(self,request,*args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class TagConfigurationTemplateViewSet(viewsets.ModelViewSet):
    """API Class View for Certificates model.
    
    Attributes:
        permission_classes (Tuple): Tuple of Permission Classes.
        queryset (QuerySet): Queryset for all certificates
        serializer_class (Object): Type of Model Serializer.

    Methods:
        list(request)
            Returns an api response of the list of certificates.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = TagConfigurationTemplateSerializer
    queryset = TagConfigurationTemplate.objects.all()

    def get_permissions(self):    
        self.permission_classes = [IsAuthenticated,IsDataValidator,]
        return super(TagConfigurationTemplateViewSet, self).get_permissions()

class ManualLogTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ManualLogTemplateSerializer
    queryset = ManualLogTemplate.objects.all()

    # def get_permissions(self):    
    #     self.permission_classes = [IsAuthenticated,IsDataValidator,]
    #     return super(TagConfigurationTemplateViewSet, self).get_permissions()

class UserActivitiesViewSet(viewsets.ModelViewSet):
    """API Class View for UserActivities model.
    
    Attributes:
        pagination_class (Object): Type of Pagination Class
        permission_classes (Object): Type of Permission Class
        queryset (Queryset): Queryset on the list of certificates ordered by
            timestamp and excluding 'IN_PROGRESS' status
        serializer_class (Object): Type of Data Serializer Class
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserActivitiesSerializer
    pagination_class = ModifiedPagination
    queryset = UserActivities.objects.all().order_by('-timestamp').exclude(status="P")