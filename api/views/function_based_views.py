""" 
Application Module for Views.
TODO: (Details)
"""


# Django Libraries
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseNotFound
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,BasePermission
#Developer Libaries
from api.models import Certificate,ExtractedDataCSV,TagConfigurationTemplate,ManualLogTemplate,CoalParameters,CoalParametersSection,CoalParametersDividers,UserActivities
from api.libs.pi.pi import *
from api.libs.consts.activitylog_status import *
from api.libs.tagconfiguration.tag_conf import preview_configuration,extract_param_tag_mapping,map_data_tagnames
from api.data_access_policy import PIDataAccessPolicy
from .lambdas import *
#Other Libraries
import pandas as pd
import os
from datetime import datetime,timedelta
from urllib.parse import urlparse

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_home(request):
    return Response({"message": "Welcome to C8-Cube API"},status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def get_user_groups(request):
    groups = request.user.groups.all()
    groups = [group.name for group in groups]
    return Response(groups,status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def extract_data(request):
    """API Functional View on extracting data.
    
    Args:
        request (Request): A request instance
    
    Returns:
        Response: An API response describing the status message of extracting data.
    """
    try:
        _id = request.query_params["_id"]
        queryset = Certificate.objects.filter(id = _id)
        cert = queryset[0]
        cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
        req_user = str(request.user)
        activity = "Extract Data from Certificate with id {}".format(_id)
        log_user_activity(req_user,activity,IN_PROGRESS)
        extract_data_background(_id,req_user,activity)
        return Response({"message" : "Data Queued for Extraction","results" : []},status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"error" : str(e)},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def view_data(request):
    """API Functional View on viewing extracted data.
    
    Args:
        request (Request): A request instance
    
    Returns:
        Response: An API response returning the results of data extration.
    """
    try:
        _id = request.query_params["_id"]
        queryset = Certificate.objects.filter(id = _id)
        cert = queryset[0]
        cert_path = os.path.join(settings.MEDIA_ROOT,str(cert.upload))
        results = check_extracted_data(_id).to_dict(orient="records")
        return Response({"message" : "Data Extracted","results" : results,"cert":{"id":cert.id,'name':cert.name,'tag_configuration_id':cert.tag_configuration_id}},status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"error" : str(e)},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def view_pdf(request):
    """API Functional View on viewing uploaded pdf file.
    
    Args:
        request (Request): A Request instance
    
    Returns:
        HttpResponse: application/pdf response of the specified certificate.
    """
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
    """API Functional View on saving edits from extracted data.
    
    Args:
        request (Request): A Request instance
    
    Returns:
        Response: An API response returning the status on saving edits from extracted data.
    """
    print("Saving edited data")
    try:
        _id = request.query_params["_id"]
        activity = "Edit Data from Certificate with id {}".format(_id)
        req_user = str(request.user)
        data_to_save = request.data
        data_df = pd.DataFrame.from_records(data_to_save)
        extracted_data_csv = ExtractedDataCSV.objects.get(id = _id)
        data_df.to_csv(extracted_data_csv.filepath, index=False)
        log_user_activity(req_user,activity,COMPLETED)
        return Response({"message" : "Edited Data Saved"},status=status.HTTP_200_OK)
    except Exception as e:
        log_user_activity(req_user,activity,FAILED)
        return Response({"message" : "Saving Failed"},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def test_pi_connection(request):
    """API Functional View on testing PI connection.
    
    Args:
        request (Request): A Request instance
    
    Returns:
        Response: An API response returning the status on testing PI Connection.
    """
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
def upload_certificate_data(request):
    """API Functional View on uploading extracted data to PI.
    
    Args:
        request (Request): A Request instance
    
    Returns:
        Response: An API response returning the status on uploading extracted data to PI.
    """

    #Request 
    _id = request.query_params["_id"]
    activity = "Upload Data from Certificate with id {}".format(_id)
    req_user = str(request.user)
    try:
        #Preprocesses df
        metadata = request.data["metadata"]
        data_to_save = request.data["piData"]
        data_df = pd.DataFrame.from_records(data_to_save)
        data_df = data_df.dropna()
        data_df['Timestamp'] = pd.to_datetime(data_df['Timestamp']) 
        data_df['Timestamp'] = data_df['Timestamp'].apply(lambda x : (x + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S.%f"))
        #Get Tag Configuration
        extracted_data_csv = ExtractedDataCSV.objects.get(id = _id)
        certificate = Certificate.objects.get(id = _id)
        try:
            tag_conf = TagConfigurationTemplate.objects.get(id=certificate.tag_configuration_id)
            reference_path = os.path.join(settings.MEDIA_ROOT,str(tag_conf.reference))
            reference_df = pd.read_csv(reference_path)
            tag_mapping = extract_param_tag_mapping(data_df,reference_df,tag_conf.transformation)
        except Exception as e:
            print(e)
            reference_df = None
            DEFAULT_QUERY = "Select Parameter,Parameter as Tagname from pi_data"
            tag_mapping = extract_param_tag_mapping(data_df,reference_df,DEFAULT_QUERY)

        data_df = pd.merge(data_df, tag_mapping, on='Parameter', how='inner')
        #Transform data for upload
        data_df['Uploaded']  = data_df.apply(
          lambda row : upload_to_pi_solo(metadata,{
              "Parameter":row["Tagname"],
              "Timestamp":row["Timestamp"],
              "Value":row["Value"]}
          ) if row["Validated"] else False,
          axis=1
        )
        count_uploaded_data = (data_df["Uploaded"]).sum()
        print(data_df.columns)
        data_df = data_df.drop(columns=["Tagname"])
        #Save state and log activity
        data_df.to_csv(extracted_data_csv.filepath, index=False)
        log_user_activity(req_user,activity,COMPLETED)
        return Response({"message" : "Certificate Data Upload Task completed. {} rows uploaded".format(count_uploaded_data)},status=status.HTTP_200_OK)
    except Exception as e:
        raise(e)
        log_user_activity(req_user,activity,FAILED)
        return Response({"message" : "Uploading Failed"},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def upload_manual_data(request):
    try:
        #Preprocesses df
        metadata = request.data["metadata"]
        data_to_save = request.data["piData"]
        data_df = pd.DataFrame.from_records(data_to_save)
        data_df = data_df.dropna()
        data_df['Timestamp'] = pd.to_datetime(data_df['Timestamp']) 
        data_df['Timestamp'] = data_df['Timestamp'].apply(lambda x : (x + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S.%f"))

        #TODO Tag Configuration

        #Transform data for upload
        data_df['Uploaded']  = data_df.apply(
                lambda row : upload_to_pi_solo(metadata,{
                    "Parameter":row["Parameter"],
                    "Timestamp":row["Timestamp"],
                    "Value":row["Value"]}
                ) if row["Validated"] else False,
                axis=1
            )
        count_uploaded_data = (data_df["Uploaded"]).sum()
        return Response({"message" : "Manual Logs Upload Task completed. {} rows uploaded".format(count_uploaded_data)},status=status.HTTP_200_OK)        
    except Exception as e:
        raise(e)
        return Response({"message" : "Uploading Failed"},status=status.HTTP_400_BAD_REQUEST)        

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def preview_configuration_api(request):
    try:
        _id = request.query_params["_id"]
        activity = "Test Configuration with certificate with id: {}".format(_id)
        req_user = str(request.user)
        reference = request.data.get('reference')

        #@print(type(reference)==InMemoryUploadedFile)
        if reference:
            if type(reference) == str:
                reference = os.path.join(settings.BASE_DIR,urlparse(reference).path.replace("/","",1))
            reference = pd.read_csv(reference)

        pi_data = check_extracted_data(_id)
        transformation = request.data.get('transformation')
        preview = preview_configuration(pi_data,reference,transformation).to_dict(orient="records")
        #print(pd.read_csv(request.data.get('reference')))
        return Response({"message" : "Sample tag/parameter map retrieved.","preview" : preview},status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"message": "Configuration Failed"},status=status.HTTP_400_BAD_REQUEST) 

@api_view(['POST'])
@permission_classes((IsAuthenticated,PIDataAccessPolicy))
def extract_manual_log_template(request):
    try:
        _id = request.query_params["_id"]
        manuallogtemplate = ManualLogTemplate.objects.get(id=_id)
        template = pd.read_csv(manuallogtemplate.template).to_dict(orient="records")
        print(template)
        return Response({"message" : "Manual Log Template retrieved.","template" : template},status=status.HTTP_200_OK)
    except Exception as e:
        print(e)