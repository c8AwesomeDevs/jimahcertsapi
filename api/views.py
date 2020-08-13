""" 
Application Module for Views.
TODO: (Details)
"""


# Django Libraries
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse, HttpResponseNotFound
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated,BasePermission
#Developer Libaries
from api.models import Certificate,ExtractedDataCSV,TagConfigurationTemplate,ManualLogTemplate,CoalParameters,CoalParametersSection,CoalParametersDividers,UserActivities
from api.serializers import CertificateSerializer,UserActivitiesSerializer,TagConfigurationTemplateSerializer,ManualLogTemplateSerializer
from api.libs.coal.controller.controller import Controller 
from api.libs.dga.dga_extractor import *
from api.libs.pi.pi import *
from api.libs.consts.activitylog_status import *
from api.libs.tagconfiguration.tag_conf import preview_configuration,extract_param_tag_mapping,map_data_tagnames
from .data_access_policy import PIDataAccessPolicy
from .pagination import ModifiedPagination
#Other Libraries
import pandas as pd
import os
from datetime import datetime,timedelta
from background_task import background
from urllib.parse import urlparse

#consts
consts_df = pd.read_csv("api\\libs\\coal\\data\\templates\\consts.csv")

#PERMISSIONS
class IsDataValidator(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='data_validator'):
            return True
        return False

#VIEWS
class CertificateViewSet(viewsets.ModelViewSet):
    """API Class View for Certificates model.
    
    Attributes:
        permission_classes (Tuple): Tuple of Permission Classes.
        queryset (QuerySet): Queryset for all certificates
        serializer_class (Object): Type of Model Serializer.

    Methods:
        list(request)
            Returns an api response of the list of certificates.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = CertificateSerializer
    queryset = Certificate.objects.all()
    def list(self, request):
        """Returns an api response of the list of certificates.
        
        Args:
            request (Request): A request instance

        Returns:
            Response: An API response of the list of certificates.
        """
        queryset = Certificate.objects.all()
        serializer = CertificateSerializer(queryset, many=True)
        user = request.user
        return Response(serializer.data)

    def partial_update(self,request,*args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class TagConfigurationTemplateViewSet(viewsets.ModelViewSet):
    """API Class View for Certificates model.
    
    Attributes:
        permission_classes (Tuple): Tuple of Permission Classes.
        queryset (QuerySet): Queryset for all certificates
        serializer_class (Object): Type of Model Serializer.

    Methods:
        list(request)
            Returns an api response of the list of certificates.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = TagConfigurationTemplateSerializer
    queryset = TagConfigurationTemplate.objects.all()

    def get_permissions(self):    
        self.permission_classes = [IsAuthenticated,IsDataValidator,]
        return super(TagConfigurationTemplateViewSet, self).get_permissions()

class ManualLogTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ManualLogTemplateSerializer
    queryset = ManualLogTemplate.objects.all()

    # def get_permissions(self):    
    #     self.permission_classes = [IsAuthenticated,IsDataValidator,]
    #     return super(TagConfigurationTemplateViewSet, self).get_permissions()

class UserActivitiesViewSet(viewsets.ModelViewSet):
    """API Class View for UserActivities model.
    
    Attributes:
        pagination_class (Object): Type of Pagination Class
        permission_classes (Object): Type of Permission Class
        queryset (Queryset): Queryset on the list of certificates ordered by
            timestamp and excluding 'IN_PROGRESS' status
        serializer_class (Object): Type of Data Serializer Class
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserActivitiesSerializer
    pagination_class = ModifiedPagination
    queryset = UserActivities.objects.all().order_by('-timestamp').exclude(status="P")


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

        # print(tag_mapping)
        # print(map_data_tagnames(data_df,tag_mapping))


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
        #Save state and log activity
        data_df.to_csv(extracted_data_csv.filepath, index=False)
        log_user_activity(req_user,activity,COMPLETED)
        return Response({"message" : "Edited Data Uploaded. {} rows uploaded".format(count_uploaded_data)},status=status.HTTP_200_OK)
    except Exception as e:
        raise(e)
        log_user_activity(req_user,activity,FAILED)
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
            print(reference)
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

#HELPER FUNCTIONS
@background(schedule=timezone.now())
def extract_data_background(_id,req_user,activity):
    """Runs a process queue on extraction on specific uploaded file on background.
    
    Args:
        _id (int): Certificate/Document ID
        req_user (str): User requesting the extraction.
        activity (str): Description of the activity.
    """
    cert = Certificate.objects.get(id = _id)
    if cert.cert_type == 'COAL': 
        extract_coal_properties(_id,req_user,activity)
    elif cert.cert_type == 'DGA':
        extract_dga_params(_id,req_user,activity)

def extract_dga_params(_id,req_user,activity):
    """Performs Data Extraction on DGA Certificates.
    
    Args:
        _id (int): Certificate/Document ID
        req_user (str): User requesting the extraction.
        activity (str): Description of the activity.
    """
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
    #Save file
    cert_name = cert.name
    cert_type = cert.cert_type
    #return Response({"message" : "Data Extracted","results" : results},status=status.HTTP_200_OK)
    _dir,filename = os.path.split(cert.upload.path)
    extracted_csv_file_path = "media\\extracted_data\\{}.csv".format(filename.replace("PDF","pdf").replace("pdf","csv"))
    save_extracted_data(_id,cert_name,cert_type,extracted_csv_file_path,final_results)
    cert.extraction_status = "E"
    cert.save() 
    log_user_activity(req_user,activity,COMPLETED)
    print("End Time : {}".format(datetime.now()))

def extract_coal_properties(_id,req_user,activity):
    """Performs Data Extraction on Coal Test/Analysis Certificates
    
    Args:
        _id (int): Certificate/Document ID
        req_user (str): User requesting the extraction.
        activity (str): Description of the activity.
    """
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
        log_user_activity(req_user,activity,COMPLETED)
    except Exception as e:
        print(e)
        cert.extraction_status = "X"
        cert.save()
        log_user_activity(req_user,activity,FAILED)
    finally:
        print("End Time : {}".format(datetime.now()))

def check_extracted_data(_id):
    """Returns if there are data extracted from a specific document
    
    Args:
        _id (int): Certificate/Document ID
    
    Returns:
        dict/bool: Dictionary of Extracted Data or False.
    """
    queryset = ExtractedDataCSV.objects.filter(id = _id)
    has_data = queryset.exists()
    if has_data:
        filepath = queryset[0].filepath
        extracted_data_df = pd.read_csv(filepath)
        extracted_data_df = extracted_data_df.where(extracted_data_df.notnull(), None)
        return extracted_data_df
    return has_data

def save_extracted_data(_id,name,cert_type,filepath,results_df):
    """Saves extracted data to a columnar data (.csv)
    
    Args:
        _id (int): Certificate/Document ID
        name (str): Document name
        cert_type (str): Document/Certificate Type
        filepath (str): Document path
        results_df (DataFrame): Dataframe representation of extracted data.
    """
    print(results_df)
    print("Saving extracted data")
    results_df.to_csv(filepath, index=False)
    extracted_data_csv = ExtractedDataCSV(id=_id,name=name,cert_type=cert_type,filepath=filepath)
    extracted_data_csv.save()

def log_user_activity(user,activity,status):
    """Logs user activities
    
    Args:
        user (str): Request User
        activity (str): Activity Description
        status (str): Activity Status
    
    Returns:
        int: UserActivity ID
    """
    timestamp = datetime.now()
    user_activity = UserActivities(user=user,activity=activity,timestamp=timestamp,status=status)
    user_activity.save()
    return user_activity.id
