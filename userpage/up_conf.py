import json
import jsonschema

class Schemas:
	def __init__(self):
		self.userpage_conf = json.load(open('/opt/easn/userpage/userpage_conf.json'))
		self.slack_oauth_response = json.load(open('/opt/easn/userpage/slack_oauth_response.json'))
		self.slack_user_identity_response = json.load(open('/opt/easn/userpage/slack_user_identity_response.json'))
		self.privs_response = json.load(open('/opt/easn/userpage/privs_response.json'))
		self.profile_response = json.load(open('/opt/easn/userpage/profile_response.json'))

def read_json_file(filename, schema):
	with open(filename) as file:
		obj = json.load(file)
		jsonschema.validate(obj, schema)
		return obj

def json_bytes(obj, schema):
	jsonschema.validate(obj, schema)
	return bytes(json.dumps(obj),'utf-8')

schema = Schemas()
userpage_conf = read_json_file('/etc/easn/userpage.conf', schema.userpage_conf)
