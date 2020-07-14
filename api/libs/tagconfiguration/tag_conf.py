import pandas as pd
from pandasql import sqldf

def preview_configuration(pi_data,reference,transformation):
	try:
		results_df = sqldf(transformation, locals()).head()
		return results_df
	except Exception as e:
		print(e)
		raise(e)
