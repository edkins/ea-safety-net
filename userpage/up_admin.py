import up_backend

def app_user_list(env, start_response):
	result = up_backend.get_user_list().json_bytes()
	start_response('200 OK', [('Content-Type', 'application/json')])
	return [result]
