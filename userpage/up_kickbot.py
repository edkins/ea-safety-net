import hashlib

from up_conf import userpage_conf
from up_conf import read_json_input
from up_conf import json_bytes
from up_conf import schema

from up_slack_kb import slack_api

class AuthorizationFailure(Exception):
	pass

def _check_slack_token(token):
	tokenhash = hashlib.sha256(bytes(token,'ascii')).hexdigest()
	if tokenhash != userpage_conf['kickbot_slack_token_hash']:
		raise AuthorizationFailure('Incorrect slack token')

def _slack_verification_response(env, start_response, req):
	obj = {'challenge':req['challenge']}
	start_response('200 OK', [('Content-Type','application/json')])
	return [json_bytes(obj, schema.slack_challenge_response)]

def _slack_event_callback(env, start_response, req):
	ev = req['event']
	if 'text' in ev and 'kick me' in ev['text'] and 'channel' in ev and 'user' in ev:
		print('Kicking a user')
		slack_api('groups.kick', {"channel":ev['channel'], "user":ev['user']})

	start_response('200 OK', [])
	return [b'']

def app_kickbot(env, start_response):
	req = read_json_input(env['wsgi.input'], schema.slack_incoming_request)
	_check_slack_token(req['token'])
	if req['type'] == 'url_verification':
		return _slack_verification_response(env, start_response, req)
	elif req['type'] == 'event_callback':
		return _slack_event_callback(env, start_response, req)
	else:
		start_response('400 Bad Request', [])
		return [b'']
