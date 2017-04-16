from http.server import HTTPServer, BaseHTTPRequestHandler

class KickBotHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.end_headers()
		self.wfile.write(bytes('Hello and stuff','utf-8'))

def run():
	server_address = ('127.0.0.1', 8080)
	httpd = HTTPServer(server_address, KickBotHandler)
	httpd.serve_forever()

run()

