"""Summary
"""
from django.db import models

# Create your models here.
class Certificate(models.Model):

	"""Summary
	
	Attributes:
	    cert_type (TYPE): Description
	    CERT_TYPES (TYPE): Description
	    COAL (str): Description
	    DGA (str): Description
	    EXTRACTED (str): Description
	    EXTRACTION_FAILED (str): Description
	    extraction_status (TYPE): Description
	    EXTRACTION_STATUSES (TYPE): Description
	    name (TYPE): Description
	    NOT_EXTRACTED (str): Description
	    QUEUED (str): Description
	    upload (TYPE): Description
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