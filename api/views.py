# DJANGO LIBRARIES
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseNotFound
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework import viewsets
from rest_access_policy import AccessPolicy
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
#from rest_framework.permissions import IsAuthenticated

#DEVELOPER LIBRARIES
from api.models import Certificate,ExtractedDataCSV,CoalParameters,CoalParametersSection,CoalParametersDividers
from api.serializers import CertificateSerializer
from api.libs.coal.controller.controller import Controller 
from api.libs.dga.dga_extractor import *
from api.libs.pi.pi import *

#OTHER LIBRARIES
import pandas as pd
import os
from datetime import datetime,timedelta
from background_task import background

#CONSTS
consts_df = pd.read_csv("api\\libs\\coal\\data\\templates\\consts.csv")

#REST ACCESS POLICY
class PIDataAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["extract_data","view_data","save_edited_data","upload_edited_data","test_pi_connection","view_pdf"],
            "principal": ["group:data_validator"],
            "effect": "allow"            
        },
        {
            "action": ["extract_data","view_pdf"],
            "principal": ["group:data_validator","group:certificate_uploader"],
            "effect": "allow"            
        }
    ]

#VIEWS
class CertificateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Certificates.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = CertificateSerializer
    queryset = Certificate.objects.all()

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def extract_data(request):
    try:
        _id = request.query_params["_id"]
        queryset = Certificate.objects.filter(id = _id)
        cert = queryset[0]
        cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
        extract_data_background(_id)
        return Response({"message" : "Data Queued for Extraction","results" : []},status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"error" : str(e)},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def view_data(request):
    try:
        _id = request.query_params["_id"]
        queryset = Certificate.objects.filter(id = _id)
        cert = queryset[0]
        cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
        results = check_extracted_data(_id)
        return Response({"message" : "Data Extracted","results" : results,"cert":{"id":cert.id,'name':cert.name}},status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"error" : str(e)},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def view_pdf(request):
    try:
        fs = FileSystemStorage()
        _id = request.query_params["_id"]
        cert = Certificate.objects.get(id=_id)
        cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
        if fs.exists(cert_path):
            with fs.open(cert_path) as pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="mypdf.pdf"'
                return response
        else:
                return HttpResponseNotFound('The requested pdf was not found in our server.')
    except Exception as e:
        return HttpResponseNotFound('The requested pdf was not found in our server.')

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
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
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def test_pi_connection(request):
    print("Testing PI connection")
    try:
        host = request.data.get("host")
        response = get_pi_connection(request)
        if response.status_code == status.HTTP_200_OK:
            dataservers_url = "{}/dataservers".format(host)
            username = request.data.get("username")
            password = request.data.get("password")
            dataservers = get_pi_dataservers(dataservers_url,username,password)
            return Response({"message" : "Connection to {} successful ".format(host),"dataservers": dataservers},status=status.HTTP_200_OK)
        else:
            return Response({"error": PI_CONNECTION_ERROR.format(host)},status=response.status_code)
    except Exception as e:
        print(e)
        return Response({"message" : "Saving Failed"},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def upload_edited_data(request):
    print("Saving edited data")
    try:
        _id = request.query_params["_id"]
        metadata = request.data["metadata"]
        data_to_save = request.data["piData"]
        data_df = pd.DataFrame.from_records(data_to_save)
        data_df['Timestamp'] = pd.to_datetime(data_df['Timestamp']) 
        data_df['Timestamp'] = data_df['Timestamp'].apply(lambda x : (x + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S.%f"))
        extracted_data_csv = ExtractedDataCSV.objects.get(id = _id)
        data_df.to_csv(extracted_data_csv.filepath, index=False)

        data_df['Uploaded']  = data_df.apply(
                lambda row : upload_to_pi_solo(metadata,{
                    "Parameter":row["Parameter"],
                    "Timestamp":row["Timestamp"],
                    "Value":row["Value"]}
                ) if row["Validated"] else False,
                axis=1
            )
        data_df.to_csv(extracted_data_csv.filepath, index=False)
        return Response({"message" : "Edited Data Uploaded"},status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"message" : "Uploading Failed"},status=status.HTTP_400_BAD_REQUEST)


#HELPER FUNCTIONS
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
            df["Validated"]  = True
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
    _dir,filename = os.path.split(cert.upload.path)
    extracted_csv_file_path = "media\\extracted_data\\{}.csv".format(filename.replace("PDF","pdf").replace("pdf","csv"))
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
        _dir,filename = os.path.split(cert.upload.path)
        extracted_csv_file_path = "media\\extracted_data\\{}.csv".format(filename.replace("PDF","pdf").replace("pdf","csv"))
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