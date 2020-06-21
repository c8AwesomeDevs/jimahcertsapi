import pandas as pd
from openpyxl import load_workbook

class Writer():
	def __init__(self,manual_logger_path):
		self.manual_logger_path = manual_logger_path

	def style_validated_data(self,val):
		print("Styling")
		return 'background-color: green' #if df["Validated"] else 'background-color: red'

	def write_to_ml(self,df):
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