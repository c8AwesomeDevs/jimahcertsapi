""" 
Application Module for Model Serializers.
TODO: (Details)
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
#from rest_framework_jwt.serializers import JSONWebTokenSerializer, jwt_payload_handler, jwt_encode_handler
from .models import Certificate,UserActivities,TagConfigurationTemplate,ManualLogTemplate
from django.contrib.auth import authenticate, user_logged_in,user_login_failed

class JWTSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
      try:
          data = super().validate(attrs)
          credentials = {
              self.username_field: attrs.get(self.username_field),
              'password': attrs.get('password')
          }
          user = authenticate(request=self.context['request'], **credentials)
          if user:
            user_logged_in.send(sender=user.__class__, request=self.context['request'], user=user)
            return data
      except Exception as e:
          raise(e)

    # def validate(self, attrs):
    #     credentials = {
    #         self.username_field: attrs.get(self.username_field),
    #         'password': attrs.get('password')
    #     }

    #     if all(credentials.values()):
    #         user = authenticate(request=self.context['request'], **credentials)

    #         if user:
    #             if not user.is_active:
    #                 msg = 'User account is disabled.'
    #                 raise serializers.ValidationError(msg)

    #             payload = jwt_payload_handler(user)
    #             user_logged_in.send(sender=user.__class__, request=self.context['request'], user=user)

    #             return {
    #                 'token': jwt_encode_handler(payload),
    #                 'user': user
    #             }
    #         else:
    #             msg = 'Unable to log in with provided credentials.'
    #             raise serializers.ValidationError(msg)
    #     else:
    #         msg = 'Must include "{username_field}" and "password".'
    #         msg = msg.format(username_field=self.username_field)
    #         raise serializers.ValidationError(msg)



class CertificateSerializer(serializers.HyperlinkedModelSerializer):
  """
    Serializer class for Certificates Model.
  """
  class Meta:
    """Meta Class for CertificateSerializer
    Attributes:
        fields (list): list of fields to serialize
        model (object): Model Class
    """
    model = Certificate
    fields = ['id','name', 'cert_type','upload','extraction_status','tag_configuration_id']

class UserActivitiesSerializer(serializers.HyperlinkedModelSerializer):
  """
    Serializer class for UserActivities Model.
  """
  class Meta:
    """Meta Class for UserActivitiesSerializer
    
    Attributes:
        fields (list): list of fields to serialize
        model (object): Model Class
    """
    model = UserActivities
    fields = ['id','user', 'timestamp','activity','status']

class TagConfigurationTemplateSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = TagConfigurationTemplate
    fields = ['id','name','transformation','reference']

class ManualLogTemplateSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = ManualLogTemplate
    fields = ['id','name', 'template']
    