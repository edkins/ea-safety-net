from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import jsonschema
import hashlib
import requests

kickbot_conf_schema = json.load(open('/opt/easn/json-schema/kickbot-conf.json'))
slack_request_schema = json.load(open('/opt/easn/json-schema/slack-request.json'))
slack_challenge_response_schema = json.load(open('/opt/easn/json-schema/slack-challenge-response.json'))

def read_json_file(filename, schema):
	with open(filename) as file:
		obj = json.load(file)
		jsonschema.validate(obj, schema)
		return obj

kickbot_conf = read_json_file('/etc/easn/kickbot.conf', kickbot_conf_schema)

def slack_api(method, data):
	data = data.copy()
	data['token'] = kickbot_conf['oauthToken']
	url = 'https://slack.com/api/'+method
	r = requests.post(url, data=data)
	r.raise_for_status()
	response = r.json()
	if 'ok' not in response or not response['ok']:
		raise ValueError('Non-ok response for slack api method ' + method)
	return response

class KickBotHandler(BaseHTTPRequestHandler):
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

	def empty_response(self):
		self.send_response(200)
		self.end_headers()

	def do_GET(self):
		self.send_error(404)

	def do_POST(self):
		if self.path == '/kickbot/slackendpoint':
			req = self.read_json(slack_request_schema)
			self.check_slack_token(req['token'])
			if req['type'] == 'url_verification':
				self.slack_verification_response(req)
			elif req['type'] == 'event_callback':
				self.slack_event_callback(req)
			else:
				self.send_error(500)
		else:
			self.send_error(404)

	def check_slack_token(self, token):
		tokenhash = hashlib.sha256(bytes(token,'ascii')).hexdigest()
		if tokenhash != kickbot_conf['slackTokenHash']:
			self.send_error(400)
			raise ValueError('Incorrect slack token')

	def slack_verification_response(self, req):
		self.json(slack_challenge_response_schema, {"challenge":req['challenge']})

	def slack_event_callback(self, req):
		ev = req['event']
		if 'text' in ev and 'kick me' in ev['text'] and 'channel' in ev and 'user' in ev:
			print('Kicking a user')
			slack_api('groups.kick', {"channel":ev['channel'], "user":ev['user']})
		self.empty_response()

def run():
	server_address = ('127.0.0.1', 8080)
	httpd = HTTPServer(server_address, KickBotHandler)
	httpd.serve_forever()

run()

