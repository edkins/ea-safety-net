import requests

from up_conf import userpage_conf

def slack_api(method, data):
	data = data.copy()
	data['token'] = userpage_conf['kickbot_oauth_token']
	url = 'https://slack.com/api/'+method
	r = requests.post(url, data=data)
	r.raise_for_status()
	response = r.json()
	if 'ok' not in response or not response['ok']:
		error = str(response['error']) if 'error' in response else 'none'
		raise ValueError('Non-ok response for slack api method ' + method + ' ' + error)
	return response
