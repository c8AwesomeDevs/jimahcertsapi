# Create your views here.
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from rest_framework import viewsets
from django.contrib.auth.models import User
from django.utils import timezone
#from rest_framework.permissions import IsAuthenticated

#Libraries
from api.models import Certificate,ExtractedDataCSV,CoalParameters,CoalParametersSection,CoalParametersDividers
from api.serializers import CertificateSerializer
from api.libs.coal.controller.controller import Controller 

import pandas as pd
import os
from datetime import datetime
from background_task import background


consts_df = pd.read_csv("api\\libs\\coal\\data\\templates\\consts.csv")

class CertificateViewSet(viewsets.ModelViewSet):
	"""
	API endpoint for Certificates.
	"""
	#permission_classes = (IsAuthenticated,)
	serializer_class = CertificateSerializer
	queryset = Certificate.objects.all()

@api_view(['POST'])
def extract_data(request):
	try:
		_id = request.query_params["_id"]
		queryset = Certificate.objects.filter(id = _id)
		cert = queryset[0]
		cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
		results = check_extracted_data(_id)
		if results:
			#print(results)
			print(cert.__dict__)
			return Response({"message" : "Data Extracted","results" : results,"cert":{"id":cert.id,'name':cert.name}},status=status.HTTP_200_OK)

		extract_data_background(_id)
		return Response({"message" : "Data Queued for Extraction","results" : []},status=status.HTTP_200_OK)
	except Exception as e:
		print(e)
		return Response({"error" : str(e)},status=status.HTTP_400_BAD_REQUEST)

def check_extracted_data(_id):
	queryset = ExtractedDataCSV.objects.filter(id = _id)
	has_data = queryset.exists()
	if has_data:
		filepath = queryset[0].filepath
		extracted_data_df = pd.read_csv(filepath)
		extracted_data_df = extracted_data_df.where(extracted_data_df.notnull(), None)
		results = extracted_data_df.to_dict(orient="records")
		return results
	return has_data

def save_extracted_data(_id,name,cert_type,filepath,results_df):
	print(results_df)
	print("Saving extracted data")
	results_df.to_csv(filepath, index=False)
	extracted_data_csv = ExtractedDataCSV(id=_id,name=name,cert_type=cert_type,filepath=filepath)
	extracted_data_csv.save()

@background(schedule=timezone.now())
def extract_data_background(_id):
	queryset = Certificate.objects.filter(id = _id)
	cert = queryset[0]
	cert.extraction_status = "Q"
	cert.save()
	cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
	print("Extracting data from {}".format(cert_path))
	print("Start Time : {}".format(datetime.now()))
	params_df = pd.DataFrame.from_records(CoalParameters.objects.all().values('section','parameters'))
	sections_df = pd.DataFrame.from_records(CoalParametersSection.objects.all().values('sections'))
	dividers_df = pd.DataFrame.from_records(CoalParametersDividers.objects.all().values('dividers'))

	min_df = consts_df[consts_df["text"]=="min"]
	max_df = consts_df[consts_df["text"]=="max"]
	cosa_3_const_df = consts_df[consts_df["text"]=="cosa-3"]
	cosa_4_1_const_df = consts_df[consts_df["text"]=="cosa-4.1"]
	args = {
		"min_df" : min_df,
		"max_df" : max_df,
		"cosa_3_const_df" : cosa_3_const_df,
		"cosa_4_1_const_df" : cosa_4_1_const_df,
		"parameters" : params_df,
		"sections" : sections_df,
		"dividers" : dividers_df,
	}
	controller = Controller(args=args)
	try:
		results = controller.process_pdf(cert_path)
		results_df = pd.DataFrame(results)
		#Save file
		cert_name = cert.name
		cert_type = cert.cert_type
		#return Response({"message" : "Data Extracted","results" : results},status=status.HTTP_200_OK)
		extracted_csv_file_path = "media\\extracted_data\\{}.csv".format(cert_name)
		save_extracted_data(_id,cert_name,cert_type,extracted_csv_file_path,results_df)
		cert.extraction_status = "E"
		cert.save()	
	except Exception as e:
		print(e)
		cert.extraction_status = "X"
		cert.save()	
	finally:
		print("End Time : {}".format(datetime.now()))