import tabula
import re

tests_keyword = "Test"
result_keywords = ["Result","Description / Visual"]

def extract_numbers_or_str(str):
    #numbers = re.findall(r'\d+\.\d+',str.replace(",","")) + re.findall(r'\d+',str.replace(",",""))
    str_arr = str.split()
    try:
        #print(str_arr)
        for _str in str_arr:
            try:
                return float(_str)
            except Exception as e:
                if _str in ['NIL','N/D']:
                    return _str
                pass
        return str
    except Exception as e:
        return str
        #return None

def get_test_name(headers):
    for header in headers:
        if "Unnamed" not in str(header):
            return header

def get_parameters(headers):
    for header in headers:
        if "Test" in str(header):
            return header

def get_values(headers):
    for header in headers:
        for result_keyword in result_keywords:
            if result_keyword in str(header):
                return header

def filter_out_uom(str):
    return str.split(",")[0]