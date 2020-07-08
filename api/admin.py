from django.contrib import admin
from .models import Certificate,ExtractedDataCSV,CoalParameters,UserActivities

# Register your models here.
admin.site.register(Certificate)
admin.site.register(ExtractedDataCSV)
admin.site.register(CoalParameters)
admin.site.register(UserActivities)