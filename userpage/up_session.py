import time
import traceback
import urllib.parse

import up_backend
from up_slack_oauth import slack_oauth
from up_conf import userpage_conf

def login_failed(env, start_response):
	start_response('401 Unauthorized', [('Content-Type', 'text/plain')])
	return [b'Login failed']

def session_timed_out(env, start_response):
	start_response('401 Unauthorized', [('Content-Type', 'text/plain')])
	return [b'Session timed out']

def redirect(path, env, start_response):
	url = env['wsgi.url_scheme'] + '://' + env['HTTP_HOST'] + path
	start_response('303 See Other', [('Content-Type', 'text/plain'),('Location',url)])
	return [b'']

def create_session(env, user_id):
	session = env['beaker.session']
	session.invalidate()
	session['user_id'] = user_id
	session.save()

def valid_session_stuff(a, env, start_response):
	session = env['beaker.session']
	if session.last_accessed == None:
		print('session.last_accessed is None')
		session.delete()
		return session_timed_out(env, start_response)
	time_elapsed = time.time() - session.last_accessed
	if time_elapsed >= userpage_conf['session_timeout_seconds']:
		print('session timed out with time elapsed ' + str(time_elapsed))
		session.delete()
		return session_timed_out(env, start_response)
	if 'user_id' not in session:
		print('user_id not in session')
		return session_timed_out(env, start_response)
	return a(env, start_response)

def valid_session(a):
	return (lambda env,start_response: valid_session_stuff(a,env,start_response))

def check_is_admin(a, env, start_response):
	user_id = env['beaker.session']['user_id']
	privs = up_backend.get_privs(user_id)
	if not privs.admin:
		start_response('401 Unauthorized', [('Content-Type', 'text/plain')])
		return [b'Unauthorized']
	return a(env, start_response)

def admin_session(a):
	return valid_session(lambda env,start_response: check_is_admin(a,env,start_response))

def app_slackauth(env, start_response):
	try:
		q = urllib.parse.parse_qs(env['QUERY_STRING'])
		code = q['code']
		resp = slack_oauth(code)
		token = resp['access_token']
		slack_team_id = resp['team']['id']
		slack_user_id = resp['user']['id']
		slack_user_name = resp['user']['name']

		user_id = up_backend.get_or_create_user_id(slack_team_id, slack_user_id, slack_user_name)
		create_session(env, user_id)

		return redirect('/static/home.html', env, start_response)
	except:
		traceback.print_exc()
		return login_failed(env,start_response)

def app_logout(env, start_response):
	session = env['beaker.session']
	session.delete()
	start_response('204 No Content', [])
	return []

