import up_conf
import requests
import jsonschema

class Post:
	def __init__(self, url, request_schema, response_schema):
		self.url = url
		self.request_schema = request_schema
		self.response_schema = response_schema

	def post(self, obj):
		jsonschema.validate(obj, self.request_schema)
		r = requests.post(self.url, data=obj)
		r.raise_for_status()
		if self.response_schema == None:
			return None
		response = r.json()
		jsonschema.validate(response, self.response_schema)
		return response

def post(url, request_schema, response_schema):
	return Post(url, request_schema, response_schema)
