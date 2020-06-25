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
from api.libs.dga.dga_extractor import *
from api.libs.pi.pi import *

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

@api_view(['POST'])
def save_edited_data(request):
    print("Saving edited data")
    try:
        _id = request.query_params["_id"]
        data_to_save = request.data
        data_df = pd.DataFrame.from_records(data_to_save)
        extracted_data_csv = ExtractedDataCSV.objects.get(id = _id)
        data_df.to_csv(extracted_data_csv.filepath, index=False)
        return Response({"message" : "Edited Data Saved"},status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message" : "Saving Failed"},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def upload_edited_data(request):
    print("Saving edited data")
    try:
        _id = request.query_params["_id"]
        data_to_save = request.data
        data_df = pd.DataFrame.from_records(data_to_save)
        extracted_data_csv = ExtractedDataCSV.objects.get(id = _id)
        data_df.to_csv(extracted_data_csv.filepath, index=False)
        print(data_df)
        return Response({"message" : "Edited Data Uploaded"},status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message" : "Saving Failed"},status=status.HTTP_400_BAD_REQUEST)

@background(schedule=timezone.now())
def extract_data_background(_id):
    cert = Certificate.objects.get(id = _id)
    if cert.cert_type == 'COAL': 
        extract_coal_properties(_id)
    elif cert.cert_type == 'DGA':
        extract_dga_params(_id)

def extract_dga_params(_id):
    cert = Certificate.objects.get(id = _id)
    cert.extraction_status = "Q"
    cert.save()
    cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
    dfs = tabula.read_pdf(cert_path, pages='all')
    print("Extracting data from {}".format(cert_path))
    print("Start Time : {}".format(datetime.now()))
    concat = []
    for df in dfs:
        test_name = get_test_name(df.columns)
        print(test_name)
        df.columns = df.iloc[0]
        try:
            df = df[1:]
            df["Parameter"] = df[get_parameters(df.columns)].apply(lambda x: ".".join([test_name,filter_out_uom(str(x))]))
            #df["Parameter"] = df[get_parameters(df.columns)].apply(lambda x: test_name if not x else  filter_out_uom(str(x)))
            df["Timestamp"] = datetime.now()
            df["Description"]  = None       
            df["Validated"]  = False        
            df['Value'] = df[get_values(df.columns)].apply(lambda x: extract_numbers_or_str(str(x)))
            df = df[~df["Parameter"].str.contains("Equipment") == True]
            concat.append(df)
        except Exception as e:
            pass
            #raise(e)
    final_results =  pd.concat(concat, axis=0)
    #Save filex
    cert_name = cert.name
    cert_type = cert.cert_type
    #return Response({"message" : "Data Extracted","results" : results},status=status.HTTP_200_OK)
    extracted_csv_file_path = "media\\extracted_data\\{}.csv".format(cert_name)
    save_extracted_data(_id,cert_name,cert_type,extracted_csv_file_path,final_results)
    cert.extraction_status = "E"
    cert.save() 
    print("End Time : {}".format(datetime.now()))

def extract_coal_properties(_id):
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