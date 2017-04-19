from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import jsonschema
import requests
import urllib.parse

userpage_conf_schema = json.load(open('/opt/easn/userpage/userpage_conf.json'))
slack_oauth_response_schema = json.load(open('/opt/easn/userpage/slack_oauth_response.json'))
slack_user_identity_response_schema = json.load(open('/opt/easn/userpage/slack_user_identity_response.json'))

class SlackServerError(Exception):
	pass

class AuthorizationFailure(Exception):
	pass

def read_json_file(filename, schema):
	with open(filename) as file:
		obj = json.load(file)
		jsonschema.validate(obj, schema)
		return obj

userpage_conf = read_json_file('/etc/easn/userpage.conf', userpage_conf_schema)

def slack_oauth(code):
	url = 'https://slack.com/api/oauth.access'
	params = {"client_id":userpage_conf['client_id'], "client_secret":userpage_conf['client_secret'], "code":code}
	r = requests.get(url, params=params)
	r.raise_for_status()
	response = r.json()
	jsonschema.validate(response, slack_oauth_response_schema)
	if not response['ok']:
		raise SlackServerError('Error from oauth.access ' + response['error'])
	if response['team']['id'] != userpage_conf['team_id']:
		raise AuthorizationFailure('Wrong team_id')
	return response

def slack_user_identity(token):
	url = 'https://slack.com/api/users.identity'
	params = {"token": token}
	r = requests.get(url, params=params)
	r.raise_for_status()
	response = r.json()
	jsonschema.validate(response, slack_user_identity_response_schema)
	if response['team']['id'] != userpage_conf['team_id']:
		raise ValueError('Wrong team_id on users.identity')
	return response['user']

class UserPageHandler(BaseHTTPRequestHandler):
	def read_json(self,schema):
		try:
			content_length = int(self.headers['Content-Length'])
			json_input = str(self.rfile.read(content_length), 'utf-8')
			obj = json.loads(json_input)
			jsonschema.validate(obj, schema)
			return obj
		except json.decoder.JSONDecodeError as e:
			self.send_error(400)
			raise e
		except jsonschema.exceptions.ValidationError as e:
			self.send_error(400)
			raise e

	def json(self, schema, obj):
		jsonschema.validate(obj, schema)
		json_data = json.dumps(obj)
		self.send_response(200)
		self.send_header('Content-Type','application/json')
		self.end_headers()
		self.wfile.write(bytes(json_data,'utf-8'))

	def do_GET(self):
		o = urllib.parse.urlparse(self.path)
		if o.path == '/userpage/slackauth':
			q = urllib.parse.parse_qs(o.query)
			self.slackauth(q['code'])
		else:
			self.send_error(404)

	def do_POST(self):
		self.send_error(404)

	def slackauth(self, code):
		try:
			resp = slack_oauth(code)
			token = resp['access_token']
			user_name = resp['user']['name']
			user_id = resp['user']['id']
			self.send_response(200)
			self.end_headers()
			self.wfile.write(bytes('Hello '+user_name,'utf-8'))
		except jsonschema.exceptions.ValidationError as e:
			self.login_failed()
			raise e
		except SlackServerError as e:
			self.login_failed()
			raise e
		except AuthorizationFailure as e:
			self.login_failed()
			raise e

	def login_failed(self):
		self.send_response(200)
		self.end_headers()
		self.wfile.write(bytes('login failed','utf-8'))

def run():
	server_address = ('127.0.0.1', 8081)
	httpd = HTTPServer(server_address, UserPageHandler)
	httpd.serve_forever()

run()

