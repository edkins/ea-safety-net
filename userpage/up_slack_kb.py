import requests

from up_conf import userpage_conf
from up_conf import schema
import api

class SlackError(Exception):
	pass

_api_kick = api.post('https://slack.com/api/groups.kick', schema.groups_kick_request, schema.groups_kick_response)

def _tok():
	return userpage_conf['kickbot_oauth_token']

def _check_ok(response, method):
	if 'ok' not in response or not response['ok']:
		error = str(response['error']) if 'error' in response else 'none'
		raise SlackError('Non-ok response for slack api method ' + method + ' ' + error)

def kick(channel, user):
	response = _api_kick.post({'token':_tok(), 'channel':channel, 'user':user})
	_check_ok(response, 'groups.kick')

