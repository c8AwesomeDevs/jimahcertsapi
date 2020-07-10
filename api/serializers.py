""" 
Application Module for Model Serializers.
TODO: (Details)
"""

from rest_framework import serializers
from .models import Certificate,UserActivities


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
		fields = ['id','name', 'cert_type','upload','extraction_status']

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