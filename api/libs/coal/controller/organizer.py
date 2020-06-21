from .helper import locate_text
import pandas as pd

class Organizer():
    def __init__(self):
        pass
    def layout_ocr_scope(self,df,template,args):
        if template == "COSA-1.1":
            regions = {
                "Properties": {}, 
                "ASH FUSION TEMPERATURE (Reducing Atmosphere)": {},
                "ASH FUSION TEMPERATURE (Oxidizing Atmosphere)": {},
            }
            param_text_location = args["Parameters"]
            test_result_text_location = args["Test Result"]
            reducing_text_location = locate_text(df,"Reducing")
            oxidizing_text_location = locate_text(df,"Oxidizing")
            
            regions["Properties"]["Param"] = (0,param_text_location["top"].iloc[0],test_result_text_location["left"].iloc[0],reducing_text_location["top"].iloc[0])
            regions["Properties"]["Values"] = (test_result_text_location["left"].iloc[0],test_result_text_location["top"].iloc[0],1650,reducing_text_location["top"].iloc[0])
            regions["ASH FUSION TEMPERATURE (Reducing Atmosphere)"]["Param"] = (0,reducing_text_location["top"].iloc[0],reducing_text_location["left"].iloc[0],1750)
            regions["ASH FUSION TEMPERATURE (Reducing Atmosphere)"]["Values"] = (reducing_text_location["left"].iloc[0],reducing_text_location["top"].iloc[0],oxidizing_text_location["left"].iloc[0],1750)
            regions["ASH FUSION TEMPERATURE (Oxidizing Atmosphere)"]["Param"] = (0,reducing_text_location["top"].iloc[0],reducing_text_location["left"].iloc[0],1750)
            regions["ASH FUSION TEMPERATURE (Oxidizing Atmosphere)"]["Values"] = (oxidizing_text_location["left"].iloc[0],oxidizing_text_location["top"].iloc[0],1650,1750)
            return regions

        elif template == "COSA-1.2":
            regions = {
                "Actual Analysis Results": {}
            }
            param_text_location = args["Parameters"]
            actual_result_text_location = args["Actual Analysis Result"]
            
            regions["Actual Analysis Results"]["Param"] = (0,param_text_location["top"].iloc[0],actual_result_text_location["left"].iloc[0],1750)
            regions["Actual Analysis Results"]["Values"] = (actual_result_text_location["left"].iloc[0],actual_result_text_location["top"].iloc[0],1650,1750)
            return regions
        elif template == "COSA-3":
            regions = {
                "Proximate Analysis": {}
            }
            proximate_analysis_text_location = args["Proximate Analysis"]
            
            regions["Proximate Analysis"]["Param"] = (0,proximate_analysis_text_location["top"].iloc[0],800,1750)
            regions["Proximate Analysis"]["Values"] = (800,proximate_analysis_text_location["top"].iloc[0],1650,1750)
            return regions
        elif template == "COSA-4.1":
            regions = {
                "Ultimate Analysis": {},
                "Ash Analysis": {},
                "Size Distribution": {}
            }
            ultimate_analysis_text_location = args["Ultimate Analysis"]
            ash_analysis_text_location = locate_text(df,"Ash Analysis")
            size_dist_text_location = locate_text(df,"Size Distribution")
            regions["Ultimate Analysis"]["Param"] = (0,ultimate_analysis_text_location["top"].iloc[0],1000,ash_analysis_text_location["top"].iloc[0])
            regions["Ash Analysis"]["Param"] = (0,ash_analysis_text_location["top"].iloc[0],1000,size_dist_text_location["top"].iloc[0])
            regions["Size Distribution"]["Param"] = (0,size_dist_text_location["top"].iloc[0],1000,1750)
            regions["Ultimate Analysis"]["Values"] = (1000,ultimate_analysis_text_location["top"].iloc[0],1650,ash_analysis_text_location["top"].iloc[0])
            regions["Ash Analysis"]["Values"] = (1000,ash_analysis_text_location["top"].iloc[0],1650,size_dist_text_location["top"].iloc[0])
            regions["Size Distribution"]["Values"] = (1000,size_dist_text_location["top"].iloc[0],1650,1750)
            return regions

    def layout_ocr_scope_optimal(self,df,template,args):
        anchors_template = pd.read_csv("api\\libs\\coal\\data\\templates\\{}.anchors".format(template))
        relations_template = pd.read_csv("api\\libs\\coal\\data\\templates\\{}.relations".format(template))    
        regions={}
        try:
            for region in relations_template["Regions"].unique():
                regions[region] = {}
                for _type in ["Param","Values"]:
                    relations = relations_template[(relations_template["Type"]==_type)&(relations_template["Regions"]==region)]
                    left_index, top_index, right_index, bottom_index = relations["Anchor_LEFT"].iloc[0],relations["Anchor_UP"].iloc[0],relations["Anchor_RIGHT"].iloc[0],relations["Anchor_DOWN"].iloc[0]
                    left_key, top_key, right_key, bottom_key =  anchors_template[anchors_template["ID"]==left_index]["Text"].iloc[0], \
                                                                anchors_template[anchors_template["ID"]==top_index]["Text"].iloc[0], \
                                                                anchors_template[anchors_template["ID"]==right_index]["Text"].iloc[0], \
                                                                anchors_template[anchors_template["ID"]==bottom_index]["Text"].iloc[0]
                    
                    left_df, top_df, right_df, bottom_df =  float(args[left_key]["left"].iloc[0]), \
                                                            float(args[top_key]["top"].iloc[0]), \
                                                            float(args[right_key]["left"].iloc[0]), \
                                                            float(args[bottom_key]["top"].iloc[0])
                    regions[region][_type] = (left_df,top_df,right_df,bottom_df)
                    #display(HTML(relations.to_html()))
            return regions
        except Exception as e:
            raise(e)

    def layout_ocr_scope_default(self,sections_df,dividers_df,min_df,max_df):
        # print(sections_df)
        # print(dividers_df)
        # print(min_df)
        # print(max_df)
        sections_values = sections_df.values.tolist()
        dividers_values = dividers_df.values.tolist()
        divider = dividers_values[0]
        min_values = min_df.values.tolist()
        max_values = max_df.values.tolist()
        regions ={}
        for i in range(0,len(sections_values)):
            region = sections_values[i][-1]
            regions[region] = {}
            try:
                regions[region]["Param"] = (0,sections_values[i][4],divider[3],sections_values[i+1][4])
                regions[region]["Values"] = (divider[3],sections_values[i][4],max_values[0][0],sections_values[i+1][4])
            except Exception as e:
                regions[region]["Param"] = (0,sections_values[i][4],divider[3],max_values[0][1])
                regions[region]["Values"] = (divider[3],sections_values[i][4],max_values[0][0],max_values[0][1])
        return regions

