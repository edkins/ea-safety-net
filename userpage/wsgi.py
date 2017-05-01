from beaker.middleware import SessionMiddleware
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import jsonschema
import requests
import selector
import time
import traceback
import urllib.parse

from up_conf import schema
from up_conf import userpage_conf
import up_backend

class SlackServerError(Exception):
	pass

class AuthorizationFailure(Exception):
	pass

def slack_oauth(code):
	url = 'https://slack.com/api/oauth.access'
	params = {"client_id":userpage_conf['client_id'], "client_secret":userpage_conf['client_secret'], "code":code}
	r = requests.get(url, params=params)
	r.raise_for_status()
	response = r.json()
	jsonschema.validate(response, schema.slack_oauth_response)
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
	jsonschema.validate(response, schema.slack_user_identity_response)
	if response['team']['id'] != userpage_conf['team_id']:
		raise ValueError('Wrong team_id on users.identity')
	return response['user']

def login_failed(env, start_response):
	start_response('401 Unauthorized', [('Content-Type', 'text/plain')])
	return [b'Login failed']

def session_timed_out(env, start_response):
	start_response('401 Unauthorized', [('Content-Type', 'text/plain')])
	return [b'Session timed out']

def create_session(env, user_id):
	session = env['beaker.session']
	session.invalidate()
	session['user_id'] = user_id
	session.save()

def redirect(path, env, start_response):
	url = env['wsgi.url_scheme'] + '://' + env['HTTP_HOST'] + path
	start_response('303 See Other', [('Content-Type', 'text/plain'),('Location',url)])
	return [b'']

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

		return redirect('/userpage/home', env, start_response)
	except:
		traceback.print_exc()
		return login_failed(env,start_response)

def app_home(env, start_response):
	session = env['beaker.session']
	start_response('200 OK', [('Content-Type', 'text/plain')])
	return [bytes('Yeah you are logged in as ' + session['user_id'],'utf-8')]

def valid_session_stuff(a, env, start_response):
	session = env['beaker.session']
	if session.last_accessed == None:
		print('session.last_accessed is None')
		return session_timed_out(env, start_response)
	time_elapsed = time.time() - session.last_accessed
	if time_elapsed >= userpage_conf['session_timeout_seconds']:
		print('session timed out with time elapsed ' + str(time_elapsed))
		return session_timed_out(env, start_response)
	if 'user_id' not in session:
		print('user_id not in session')
		return session_timed_out(env, start_response)
	return a(env, start_response)

def valid_session(a):
	return (lambda env,start_response: valid_session_stuff(a,env,start_response))

app = selector.Selector()
app.add('/userpage/slackauth', GET=app_slackauth)
app.add('/userpage/home', GET=valid_session(app_home))

beaker_config = {'session.key':'id','session.type':'file','session.data_dir':'/var/easn/userpage/beaker','session.cookie_expires':'true','session.secure':'true'}

application = SessionMiddleware(app, beaker_config)
