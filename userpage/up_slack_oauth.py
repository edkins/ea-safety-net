from up_conf import schema
from up_conf import userpage_conf
import requests
import jsonschema

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
		raise AuthorizationFailure('Error from oauth.access ' + response['error'])
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
		raise AuthorizationFailure('Wrong team_id on users.identity')
	return response['user']

