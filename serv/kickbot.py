from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import jsonschema
import hashlib

kickbot_conf_schema = json.load(open('/opt/easn/json-schema/kickbot-conf.json'))
slack_request_schema = json.load(open('/opt/easn/json-schema/slack-request.json'))
slack_challenge_response_schema = json.load(open('/opt/easn/json-schema/slack-challenge-response.json'))

def read_json_file(filename, schema):
	with open(filename) as file:
		obj = json.load(file)
		jsonschema.validate(obj, schema)
		return obj

kickbot_conf = read_json_file('/etc/easn/kickbot.conf', kickbot_conf_schema)

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

	def do_GET(self):
		#self.send_response(200)
		#self.end_headers()
		#self.wfile.write(bytes('Hello and stuff','utf-8'))
		self.send_error(404)

	def do_POST(self):
		if self.path == '/kickbot/slackendpoint':
			req = self.read_json(slack_request_schema)
			if req['type'] == 'url_verification':
				self.slack_verification(req)
			else:
				self.send_error(500)
		else:
			self.send_error(404)

	def slack_verification(self, req):
		tokenhash = hashlib.sha256(bytes(req['token'],'ascii')).hexdigest()
		if tokenhash != kickbot_conf['slackTokenHash']:
			self.send_error(400)
			raise ValueError('Incorrect slack token')
		self.json(slack_challenge_response_schema, {"challenge":req['challenge']})

def run():
	server_address = ('127.0.0.1', 8080)
	httpd = HTTPServer(server_address, KickBotHandler)
	httpd.serve_forever()

run()

