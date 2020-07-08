from django.db import models

# Create your models here.
class Certificate(models.Model):
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
		return "{}-{}".format(self.id,self.name)

class ExtractedDataCSV(models.Model):
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
		return "{}-{}".format(self.id,self.name)

class UserActivities(models.Model):
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
	section = models.CharField(max_length=100)
	parameters = models.CharField(max_length=100)

class CoalParametersSection(models.Model):
	sections = models.CharField(max_length=100)

class CoalParametersDividers(models.Model):
	dividers = models.CharField(max_length=100)