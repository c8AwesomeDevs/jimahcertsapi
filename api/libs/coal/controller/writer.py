"""Summary
"""
import pandas as pd
from openpyxl import load_workbook

class Writer():

	"""Summary
	
	Attributes:
	    manual_logger_path (TYPE): Description
	"""
	
	def __init__(self,manual_logger_path):
		"""Summary
		
		Args:
		    manual_logger_path (TYPE): Description
		"""
		self.manual_logger_path = manual_logger_path

	def style_validated_data(self,val):
		"""Summary
		
		Args:
		    val (TYPE): Description
		
		Returns:
		    TYPE: Description
		"""
		print("Styling")
		return 'background-color: green' #if df["Validated"] else 'background-color: red'

	def write_to_ml(self,df):
		"""Summary
		
		Args:
		    df (TYPE): Description
		"""
		print("Writing to {}".format(self.manual_logger_path))
		try:
			writer = pd.ExcelWriter(self.manual_logger_path, engine='openpyxl')
			writer.book = load_workbook(self.manual_logger_path)
			writer.sheets = dict((ws.title, ws) for ws in writer.book.worksheets)
			reader = pd.read_excel(self.manual_logger_path,sheet_name="PDF")
			df.to_excel(writer,sheet_name="PDF",index=False,header=False,startrow=len(reader)+1)
			writer.close()
		except Exception as e:
			print(e)
			writer.close()