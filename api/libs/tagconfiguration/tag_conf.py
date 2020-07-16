import pandas as pd
from pandasql import sqldf

def preview_configuration(pi_data,reference,transformation):
	"""Summary
	
	Args:
	    pi_data (TYPE): Description
	    reference (TYPE): Description
	    transformation (TYPE): Description
	
	Returns:
	    TYPE: Description
	"""
	try:
		results_df = sqldf(transformation, locals()).head()
		return results_df
	except Exception as e:
		print(e)
		raise(e)

def extract_param_tag_mapping(pi_data,reference,transformation):
	"""Summary
	
	Args:
	    pi_data (TYPE): Description
	    reference (TYPE): Description
	    transformation (TYPE): Description
	
	Returns:
	    TYPE: Description
	"""
	try:
		results_df = sqldf(transformation, locals())
		return results_df
	except Exception as e:
		print(e)
		raise(e)

def map_data_tagnames(pi_data,tagname_map):
	try:
		transformation = "Select pi_data.Parameter,tagname_map.Tagname,pi_data.Timestamp,pi_data.Value,pi_data.Validated,pi_data.Uploaded \
						from pi_data inner join tagname_map on pi_data.Parameter = tagname_map.Parameter"
		results_df = sqldf(transformation, locals())
		return results_df
	except Exception as e:
		raise(e)
