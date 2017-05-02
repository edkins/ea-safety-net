import up_backend

def app_privs(env, start_response):
	user_id = env['beaker.session']['user_id']
	result = up_backend.get_privs(user_id).json_bytes()
	start_response('200 OK', [('Content-Type', 'application/json')])
	return [result]

def app_profile(env, start_response):
	user_id = env['beaker.session']['user_id']
	result = up_backend.get_profile(user_id).json_bytes()
	start_response('200 OK', [('Content-Type', 'application/json')])
	return [result]

