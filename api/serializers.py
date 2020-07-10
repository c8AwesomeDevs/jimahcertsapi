from rest_framework import serializers
from .models import Certificate,UserActivities


class CertificateSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:

		"""Summary
		Attributes:
		    fields (list): Description
		    model (TYPE): Description
		"""
		model = Certificate
		fields = ['id','name', 'cert_type','upload','extraction_status']

class UserActivitiesSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		"""Summary
		
		Attributes:
		    fields (list): Description
		    model (TYPE): Description
		"""
		model = UserActivities
		fields = ['id','user', 'timestamp','activity','status']