"""Summary
"""
from pdf2image import convert_from_path
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
from fuzzywuzzy import fuzz

from .ocr import OCR
from .classifier import Classifier,keys
from .organizer import Organizer
from .helper import locate_text,filter_values_only
from .writer import Writer

class Controller():

    """Summary
    
    Attributes:
        args (TYPE): Description
        classifier (TYPE): Description
        ocr (TYPE): Description
        organizer (TYPE): Description
    """
    
    def __init__(self,manual_logger_path=None,args=None):
        """Summary
        
        Args:
            manual_logger_path (None, optional): Description
            args (None, optional): Description
        """
        #self.excel_writer =  Writer(manual_logger_path)
        self.ocr = OCR()
        self.classifier = Classifier(self.ocr)
        self.organizer = Organizer()
        self.args = args

    def align_params_values(self,params,values):
        """Summary
        
        Args:
            params (TYPE): Description
            values (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        extracted_data_aligned = []
        for row in values.iterrows():
            top = row[1]["top"]
            text = row[1]["text"]
            #print(top,text)
            for param in params.iterrows():
                param_top = param[1]["top"]
                param_text = param[1]["text"]
                if abs(top-param_top) <= 20:
                    #print(param_text,",",text)
                    extracted_data_aligned.append([param_text,text])
                    break

        extracted_data_aligned_df = pd.DataFrame(extracted_data_aligned)
        try:
            extracted_data_aligned_df.columns= ["Parameter","Value"]
        except Exception as e:
            print(e)
        return extracted_data_aligned_df

    def validate_parameters(self,test_param_df,true_param_df):
        """Summary
        
        Args:
            test_param_df (TYPE): Description
            true_param_df (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        section = test_param_df.columns[0]
        #test_param_df[section] = test_param_df[section].apply(lambda x:"{}***Unvalidated***".format(x))
        filtered_true_param_df =  true_param_df[true_param_df["section"]==section]["parameters"]
        columns = filtered_true_param_df.tolist()
        indexes = test_param_df[section].tolist()
        score_matrix = []
        score_matrix_max = {}
        for test_param in indexes:
            temp = []
            final_score = 0
            final_param = test_param
            validated = False
            for true_param in columns:
                ratio = fuzz.ratio(true_param,test_param)
                partial_ratio = fuzz.partial_ratio(true_param,test_param)
                token_sort_ratio = fuzz.token_sort_ratio(true_param,test_param)
                #print("{} || {} \t Ratio: {}\t Partial Ratio{}\t Token Sort Ratio: {}\n".format(true_param,test_param,ratio,partial_ratio,token_sort_ratio))
                score = max(ratio,partial_ratio,token_sort_ratio)
                if score > final_score and score >=75:
                    final_score = score
                    final_param = true_param
                    validated = True
                temp.append(score)
            score_matrix.append(temp)
            score_matrix_max[test_param] = (final_score,final_param,validated)
        
        distance_matrix = pd.DataFrame(data=score_matrix, index=indexes, columns=columns)
        test_param_df["Validated"] = test_param_df[section].apply(lambda x:score_matrix_max[x][2])
        test_param_df["Uploaded"] = False
        test_param_df[section] = test_param_df[section].apply(lambda x:score_matrix_max[x][1])
        return test_param_df

    def process_image(self,image,ocr_results_df,template,args):
        """Summary
        
        Args:
            image (TYPE): Description
            ocr_results_df (TYPE): Description
            template (TYPE): Description
            args (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        results = []
        try:
            if not template=="default":
                regions = self.organizer.layout_ocr_scope_optimal(ocr_results_df,template,args)
            else:
                sections_df = args["sections_df"]
                dividers_df = args["dividers_df"]
                regions = self.organizer.layout_ocr_scope_default(sections_df,dividers_df,self.args['min_df'],self.args['max_df'])
            for region in regions: 
                param_region = regions[region]["Param"]
                values_region = regions[region]["Values"]
                #parameters = self.args["parameters"]

                param_image_cropped = image.crop(param_region)
                ocr_results_params_df = self.ocr.filter_ocr_results(self.ocr.get_ocr_results(param_image_cropped))
                values_image_cropped = image.crop(values_region)
                ocr_results_values_df = self.ocr.filter_ocr_results(self.ocr.get_ocr_results(values_image_cropped))
                ocr_results_values_df_filtered =  filter_values_only(ocr_results_values_df)
                final_results =  self.align_params_values(ocr_results_params_df,ocr_results_values_df_filtered)
                
                final_results.columns = [region,"Value"] 
                final_results = self.validate_parameters(final_results,self.args["parameters"]) 

                final_results.columns = ["Parameter","Value","Validated","Uploaded"]
                final_results["Parameter"] = final_results["Parameter"].apply(lambda x : "{}.{}".format(region,x))
                final_results["Select"] = 'x'
                final_results["Server"] = 'CALIBR8'
                final_results["Timestamp"] = datetime.now()
                final_results["Description"]  = None
                final_results = final_results[["Select","Server","Parameter","Description","Timestamp","Value","Validated","Uploaded"]]
                #self.excel_writer.write_to_ml(final_results)
                #print(final_results)
                #results[region] = final_results.to_dict(orient="records")
                #print(final_results.to_dict(orient="records"))
                results += final_results.to_dict(orient="records")

            #print(results)
            return results
        except Exception as e:
            raise(e)

    def organize_regions_default(self,sections_df,dividers_df):
        """Summary
        
        Args:
            sections_df (TYPE): Description
            dividers_df (TYPE): Description
        """
        pass

    def process_pdf(self,pdf_path):
        """Summary
        
        Args:
            pdf_path (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        images = convert_from_path(pdf_path)
        classifications = self.classifier.classify_pages_based_on_keys(images,keys)
        min_df = self.args["min_df"]
        max_df = self.args["max_df"]
        cosa_3_const_df = self.args["cosa_3_const_df"]
        cosa_4_1_const_df = self.args["cosa_4_1_const_df"]

        extraction_results = []

        for key in classifications:
            image_template_tuple_arr = []
            for image in classifications[key]:
                if key == 'cosa_cert'  or key == 'coa_cert':
                    ocr_results_df = self.ocr.get_ocr_results(image)
                    ocr_results_filtered = self.ocr.filter_ocr_results(ocr_results_df)
                    param_text_location = locate_text(ocr_results_df,"Parameters")
                    prop_text_location = locate_text(ocr_results_df,"PROPERTY")
                    proximate_analysis_text_location = locate_text(ocr_results_filtered,"Proximate Analysis")
                    if not param_text_location.empty:
                        #print("Parameters : ",param_text_location)
                        test_result_text_location = locate_text(ocr_results_df,"Test")
                        actual_result_text_location = locate_text(ocr_results_df,"Actual")
                        if not test_result_text_location.empty:
                            print("1.1")
                            reducing_text_location = locate_text(ocr_results_df,"Reducing")
                            oxidizing_text_location = locate_text(ocr_results_df,"Oxidizing")
                            args = {
                                "Parameters" : param_text_location,
                                "Test Result" : test_result_text_location,
                                "ASH FUSION TEMPERATURE (Reducing Atmosphere)": reducing_text_location,
                                "ASH FUSION TEMPERATURE (Oxidizing Atmosphere)": oxidizing_text_location,   
                                "min" :min_df,
                                "max" : max_df
                            }
                            extraction_result = self.process_image(image,ocr_results_df,"COSA-1.1",args)
                            extraction_results += extraction_result
                        elif not actual_result_text_location.empty:
                            print("1.2")
                            args = {
                                "Parameters" : param_text_location,
                                "Actual Analysis Result" : actual_result_text_location,
                                "min" :min_df,
                                "max" : max_df
                            }
                            extraction_result = self.process_image(image,ocr_results_df,"COSA-1.2",args)
                            extraction_results += extraction_result
                    elif not prop_text_location.empty:
                        result_text_location = locate_text(ocr_results_df,"RESULT")
                        value_text_location = locate_text(ocr_results_df,"VALUE")
                        if not result_text_location.empty:
                            print("2.0")
                            args = {
                                "Property" : prop_text_location,
                                "Result" : result_text_location,
                                "Proximate Analysis" : proximate_analysis_text_location,
                                "min" :min_df,
                                "max" : max_df
                            }
                            extraction_result = self.process_image(image,ocr_results_df,"COSA-2.0",args)
                            extraction_results += extraction_result
                        elif not value_text_location.empty:
                            print("2.1")
                            args = {
                                "Property" : prop_text_location,
                                "Value" : value_text_location,
                                "Proximate Analysis" : proximate_analysis_text_location,
                                "min" :min_df,
                                "max" : max_df
                            }
                            extraction_result = self.process_image(image,ocr_results_df,"COSA-2.1",args)
                            extraction_results += extraction_result
                    elif not proximate_analysis_text_location.empty:
                        print("3.0")
                        args = {
                            "Proximate Analysis" : proximate_analysis_text_location,
                            "cosa-3" : cosa_3_const_df,
                            "min" :min_df,
                            "max" : max_df                    
                        }
                        extraction_result = self.process_image(image,ocr_results_df,"COSA-3",args)
                        extraction_results += extraction_result
                elif key == "cosa_cert_att":
                    ocr_results_df = self.ocr.get_ocr_results(image)
                    ocr_results_filtered = self.ocr.filter_ocr_results(ocr_results_df)
                    ultimate_analysis_text_location  = locate_text(ocr_results_filtered,"ULTIMATE ANALYSIS")
                    aft_text_location  = locate_text(ocr_results_filtered,"Ash Fusion Temperature")
                    value_text_location = locate_text(ocr_results_filtered,"Value")
                    if not aft_text_location.empty:
                        print("4.2")                        
                        aft_redux_text_location = aft_text_location.iloc[0:1]
                        aft_oxidize_text_location = aft_text_location.iloc[1:]
                        prop_text_location = locate_text(ocr_results_filtered,"Physical Properties")
                        ash_analysis_text_location = locate_text(ocr_results_filtered,"Ash Analysis")
                        value_text_location = locate_text(ocr_results_df,"Value") if not locate_text(ocr_results_df,"Value").empty else cosa_4_1_const_df
                        args = {
                            "Ultimate Analysis" : ultimate_analysis_text_location,
                            "Reducing Atmosphere" : aft_redux_text_location,
                            "Oxidizing Atmosphere" : aft_oxidize_text_location,
                            "Physical Properties" : prop_text_location,
                            "Ash Analysis" : ash_analysis_text_location,
                            "Value" : value_text_location,
                            "min" :min_df,
                            "max" : max_df                    
                        }   

                        extraction_result = self.process_image(image,ocr_results_filtered,"COSA-4.2",args) 
                        extraction_results += extraction_result             
                    else:
                        print("4.1")                        
                        ash_analysis_text_location = locate_text(ocr_results_filtered,"Ash Analysis")
                        size_dist_text_location = locate_text(ocr_results_filtered,"Size Distribution")
                        args = {
                            "Ultimate Analysis" : ultimate_analysis_text_location,
                            "Ash Analysis" : ash_analysis_text_location,
                            "Size Distribution" : size_dist_text_location,
                            "cosa-4.1" : cosa_4_1_const_df,
                            "min" :min_df,
                            "max" : max_df                    
                        }                
                        extraction_result = self.process_image(image,ocr_results_filtered,"COSA-4.1",args)
                        extraction_results += extraction_result

        return extraction_results


    def process_pdf_default(self,pdf_path):
        """Summary
        
        Args:
            pdf_path (TYPE): Description
        """
        images = convert_from_path(pdf_path)
        classifications = self.classifier.classify_pages_based_on_keys(images,keys)
        min_df = self.args["min_df"]
        max_df = self.args["max_df"]

        for key in classifications:
            image_template_tuple_arr = []
            for image in classifications[key]:
                ocr_results_df = self.ocr.get_ocr_results(image)
                ocr_results_filtered = self.ocr.filter_ocr_results(ocr_results_df)
                sections_df = pd.DataFrame(columns=["block","paragraph","line","left","top","text","section"])
                dividers_df = pd.DataFrame(columns=["block","paragraph","line","left","top","text"])
                for section in self.args["sections"]["Sections"]:
                    text_location = locate_text(ocr_results_filtered,section)
                    text_location["section"] = section
                    sections_df = pd.concat([sections_df,text_location])

                for divider in self.args["dividers"]["Dividers"]:
                    text_location = locate_text(ocr_results_df,divider,0)
                    text_location = text_location[["block_num","par_num","line_num","left","top","text"]]
                    text_location.columns = ["block","paragraph","line","left","top","text"]
                    dividers_df = pd.concat([dividers_df,text_location])

                sections_df = sections_df.sort_values('top')
                dividers_df = dividers_df.sort_values('top')
                args = {
                    "sections_df" : sections_df,
                    "dividers_df" : dividers_df
                }

                self.process_image(image,ocr_results_filtered,"default",args)


