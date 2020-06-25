import requests
import json

def get_pi_connection(request):
	try:
		host = request.data.get("host")
		username = request.data.get("username")
		password = request.data.get("password")
		response = requests.get(host,auth=(username,password),verify=False)
		return response
	except Exception as e:
		print(e)
		raise e

def upload_to_pi(request):
	try:
		host = request.data.get("host")
		username = request.data.get("username")
		password = request.data.get("password")
		auth = (username,password)
		data_archive = request.data.get("dataArchive")
		data_set = request.data.get("dataSet")

		for key in data_set:
			endpoint = "{}/points?path=\\\\{}\\{}".format(host,data_archive,key)
			web_id = get_web_id(endpoint,auth)
			if web_id:
				data = data_set[key]
				values_endpoint = "{}/streams/{}/recorded".format(host,web_id,data)

		return True
	except Exception as e:
		print(e)
		return False
		#raise e

def get_web_id(endpoint,auth):
	try:
		resp = requests.get(endpoint,auth=auth,verify=False)
		return resp.json()['WebId']
	except Exception as e:
		print(e)
		return None

def upload_bulk(endpoint,auth,data):
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