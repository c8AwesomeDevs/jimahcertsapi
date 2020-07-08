from rest_framework import serializers
from .models import Certificate,UserActivities


class CertificateSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Certificate
		fields = ['id','name', 'cert_type','upload','extraction_status']

class UserActivitiesSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = UserActivities
		fields = ['id','user', 'timestamp','activity','status']