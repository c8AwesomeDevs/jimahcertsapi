"""Summary
"""
import requests
import json

def get_pi_connection(request):
	"""Summary
	
	Args:
	    request (TYPE): Description
	
	Returns:
	    TYPE: Description
	
	Raises:
	    e: Description
	"""
	try:
		host = request.data.get("host")
		username = request.data.get("username")
		password = request.data.get("password")
		response = requests.get(host,auth=(username,password),verify=False)
		return response
	except Exception as e:
		print(e)
		raise e

def get_pi_dataservers(daservers_url,username,password):
	"""Summary
	
	Args:
	    daservers_url (TYPE): Description
	    username (TYPE): Description
	    password (TYPE): Description
	
	Returns:
	    TYPE: Description
	
	Raises:
	    e: Description
	"""
	try:
		response = requests.get(daservers_url,auth=(username,password),verify=False)
		return response.json()["Items"]
	except Exception as e:
		print(e)
		raise e

def upload_to_pi(metadata,data_dict):
	"""Summary
	
	Args:
	    metadata (TYPE): Description
	    data_dict (TYPE): Description
	
	Returns:
	    TYPE: Description
	"""
	try:
		print("Uploading data")
		host = metadata.get("host")
		username = metadata.get("username")
		password = metadata.get("password")
		auth = (username,password)
		data_archive = metadata.get("da")

		for record in data_dict:
			param = record['Parameter']
			endpoint = "https://{}/piwebapi/points?path=\\\\{}\\{}".format(host,data_archive,param)
			web_id = get_web_id(endpoint,auth)
			if web_id:
				try:
					data = {
						"Timestamp" : record['Timestamp'],
						"Value" : record['Value']
					}
					values_endpoint = "https://{}/piwebapi/streams/{}/value".format(host,web_id)
					headers = {
						"X-Requested-With" : "message/http",
						"Content-Type" : "application/json"
					}
					resp = requests.post(values_endpoint,auth=auth,data=json.dumps(data),headers=headers,verify=False)
				except Exception as e:
					print(e)

		return True
	except Exception as e:
		print(e)
		return False
		#raise e

def upload_to_pi_solo(metadata,record):
	"""Summary
	
	Args:
	    metadata (TYPE): Description
	    record (TYPE): Description
	
	Returns:
	    TYPE: Description
	"""
	try:
		host = metadata.get("host")
		username = metadata.get("username")
		password = metadata.get("password")
		auth = (username,password)
		data_archive = metadata.get("da")
		param = record['Parameter']
		endpoint = "https://{}/piwebapi/points?path=\\\\{}\\{}".format(host,data_archive,param)
		web_id = get_web_id(endpoint,auth)
		if web_id:
			try:
				data = {
					"Timestamp" : record['Timestamp'],
					"Value" : record['Value']
				}
				values_endpoint = "https://{}/piwebapi/streams/{}/value".format(host,web_id)
				headers = {
					"X-Requested-With" : "message/http",
					"Content-Type" : "application/json"
				}
				resp = requests.post(values_endpoint,auth=auth,data=json.dumps(data),headers=headers,verify=False)
				if resp.status_code == 200 or resp.status_code == 202:
					return True
				return False				
			except Exception as e:
				#print(e)
				pass
		return False
	except Exception as e:
		#print(e)
		return False

def get_web_id(endpoint,auth):
	"""Summary
	
	Args:
	    endpoint (TYPE): Description
	    auth (TYPE): Description
	
	Returns:
	    TYPE: Description
	"""
	try:
		resp = requests.get(endpoint,auth=auth,verify=False)
		return resp.json()['WebId']
	except Exception as e:
		#print(e)
		return None

def upload_bulk(endpoint,auth,data):
	"""Summary
	
	Args:
	    endpoint (TYPE): Description
	    auth (TYPE): Description
	    data (TYPE): Description
	
	Returns:
	    TYPE: Description
	"""
	try:
		print(endpoint)
		print(auth)
		print(data)
		print(type(data))
		headers = {
			"X-Requested-With" : "message/http",
			"Content-Type" : "application/json"
		}
		resp = requests.post(endpoint,auth=auth,data=json.dumps(data),headers=headers,verify=False)
		print(resp.status_code)
		return resp
	except Exception as e:
		print(e)
		return None