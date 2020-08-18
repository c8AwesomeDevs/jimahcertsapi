""" 
Application Module for Models.
TODO: (Details)
"""

from django.db import models

# Create your models here.
class UserLoginActivity(models.Model):
    # Login Status
    SUCCESS = 'S'
    FAILED = 'F'

    LOGIN_STATUS = ((SUCCESS, 'Success'),
                           (FAILED, 'Failed'))

    login_IP = models.GenericIPAddressField(null=True, blank=True)
    login_datetime = models.DateTimeField(auto_now=True)
    login_username = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=1, default=SUCCESS, choices=LOGIN_STATUS, null=True, blank=True)
    user_agent_info = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'user_login_activity'
        verbose_name_plural = 'user_login_activities'

class Certificate(models.Model):

	"""Model Class for Certificates/Document
	
	Attributes:
	    cert_type (models.CharField): Certificate Type Field
	    CERT_TYPES (list): List of tuples on different certificate types
	    extraction_status (models.CharField): Certificate Extraction Status Field
	    name (models.CharField)): Certificate/Document name Field
	    upload (models.FileField): Certificate File Field
	"""
	
	name = models.CharField(max_length=100)
	COAL = 'COAL'
	DGA = 'DGA'
	CERT_TYPES = [
		(COAL, 'Coal Sampling and Analysis Certificate'),
		(DGA, 'DGA Test Certificate')
	]
	cert_type = models.CharField(
		max_length=4,
		choices=CERT_TYPES,
		default=COAL,
	)
	upload = models.FileField(upload_to='uploads\\')
	EXTRACTED = "E"
	QUEUED = "Q"
	NOT_EXTRACTED = "NE"
	EXTRACTION_FAILED = "X"
	EXTRACTION_STATUSES = [
		(EXTRACTED, 'Extracted'),
		(QUEUED, 'Queued'),
		(NOT_EXTRACTED,'Not Extracted'),
		(EXTRACTION_FAILED,'Extraction Failed')
	]
	extraction_status = models.CharField(
		max_length=2,
		choices=EXTRACTION_STATUSES,
		default=NOT_EXTRACTED,
	)
	tag_configuration_id = models.IntegerField(default=-1)


	def __str__(self):
		"""Summary
		
		Returns:
		    TYPE: Description
		"""
		return "{}-{}".format(self.id,self.name)

class ExtractedDataCSV(models.Model):

	"""Summary
	
	Attributes:
	    cert_type (TYPE): Description
	    CERT_TYPES (TYPE): Description
	    COAL (str): Description
	    DGA (str): Description
	    filepath (TYPE): Description
	    name (TYPE): Description
	"""
	
	name = models.CharField(max_length=100)
	COAL = 'COAL'
	DGA = 'DGA'
	CERT_TYPES = [
		(COAL, 'Coal Sampling and Analysis Certificate'),
		(DGA, 'DGA Test Certificate')
	]
	cert_type = models.CharField(
		max_length=4,
		choices=CERT_TYPES,
		default=COAL,
	)
	filepath = models.CharField(max_length=100)

	def __str__(self):
		"""Summary
		
		Returns:
		    TYPE: Description
		"""
		return "{}-{}".format(self.id,self.name)

class TagConfigurationTemplate(models.Model):

	"""Summary
	
	Attributes:
	    conf_type (TYPE): Description
	    CONFIGURATION_TYPES (TYPE): Description
	    name (TYPE): Description
	    references (TYPE): Description
	    transformers (TYPE): Description
	"""
	
	name = models.CharField(max_length=100)
	transformation = models.CharField(max_length=9999)
	reference = models.FileField(upload_to='configurations\\',blank = True)

	def __str__(self):
		"""Summary
		
		Returns:
		    TYPE: Description
		"""
		return "{}-{}".format(self.id,self.name)


class ManualLogTemplate(models.Model):

	name = models.CharField(max_length=100)
	template = models.FileField(upload_to='manuallogs\\',blank = True)

	def __str__(self):
		"""Summary
		
		Returns:
		    TYPE: Description
		"""
		return "{}-{}".format(self.id,self.name)

class DigitalStates(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(max_length=100)

class UserActivities(models.Model):

	"""Summary
	
	Attributes:
	    activity (TYPE): Description
	    COMPLETED (str): Description
	    FAILED (str): Description
	    IN_PROGRESS (str): Description
	    status (TYPE): Description
	    STATUSES (TYPE): Description
	    timestamp (TYPE): Description
	    user (TYPE): Description
	"""
	
	user = models.CharField(max_length=100)
	timestamp = models.DateTimeField()
	activity = models.CharField(max_length=500)
	
	IN_PROGRESS = "P"
	COMPLETED = "C"
	FAILED = "X"
	STATUSES = [
		(IN_PROGRESS,'In Progress'),
		(COMPLETED,'Completed'),
		(FAILED,'Failed')
	]
	status = models.CharField(
		max_length=4,
		choices=STATUSES,
		default=IN_PROGRESS,
	)

class CoalParameters(models.Model):

	"""Summary
	
	Attributes:
	    parameters (TYPE): Description
	    section (TYPE): Description
	"""
	
	section = models.CharField(max_length=100)
	parameters = models.CharField(max_length=100)

class CoalParametersSection(models.Model):

	"""Summary
	
	Attributes:
	    sections (TYPE): Description
	"""
	
	sections = models.CharField(max_length=100)

class CoalParametersDividers(models.Model):

	"""Summary
	
	Attributes:
	    dividers (TYPE): Description
	"""
	
	dividers = models.CharField(max_length=100)