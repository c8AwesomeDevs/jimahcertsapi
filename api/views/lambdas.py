# """ 
# Application Module for Views.
# TODO: (Details)
# """


# # Django Libraries
from django.conf import settings
from django.utils import timezone
#Developer Libaries
from api.models import Certificate,ExtractedDataCSV,TagConfigurationTemplate,ManualLogTemplate,CoalParameters,CoalParametersSection,CoalParametersDividers,UserActivities
from api.libs.coal.controller.controller import Controller 
from api.libs.dga.dga_extractor import *
from api.libs.consts.activitylog_status import *
#Other Libraries
import pandas as pd
import os
from datetime import datetime,timedelta
from background_task import background

#consts
consts_df = pd.read_csv("api\\libs\\coal\\data\\templates\\consts.csv")

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
        df.columns = df.iloc[0]
        try:
            df = df[1:]
            df["Parameter"] = df[get_parameters(df.columns)].apply(lambda x: ".".join([test_name,filter_out_uom(str(x))]))
            #df["Parameter"] = df[get_parameters(df.columns)].apply(lambda x: test_name if not x else  filter_out_uom(str(x)))
            df["Timestamp"] = datetime.now()
            df["Validated"]  = True
            df["Uploaded"]  = False
            df['Value'] = df[get_values(df.columns)].apply(lambda x: extract_numbers_or_str(str(x)))
            df = df[~df["Parameter"].str.contains("Equipment") == True]
            concat.append(df)
        except Exception as e:
            pass
            #raise(e)
    final_results =  pd.concat(concat, axis=0)
    final_results = final_results[["Parameter","Timestamp","Value","Validated",'Uploaded']]
    #final_results.columns = ["Parameter","Description","Timestamp","Value","Validated",'Uploaded']
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
        results_df["Uploaded"] = False
        results_df = results_df[["Parameter","Timestamp","Value","Validated",'Uploaded']]
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