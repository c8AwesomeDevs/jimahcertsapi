import enum
from datetime import datetime

class PIDataTypes(enum.Enum):
	FLOAT = "FLOAT"
	INT = "INTEGER"
	STR = "STRING"
	TIMESTAMP = "TIMESTAMP"
	DIGSTATE = "DIGITAL STATE"

def transform(value,data_type):
	try:
		
	except Exception as e:
		return value