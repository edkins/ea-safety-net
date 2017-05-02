import up_backend

from up_slack_kb import groups_list
from up_slack_kb import slack_team_id
from up_conf import json_bytes
from up_conf import read_json_input
from up_conf import schema

def app_user_list(env, start_response):
	result = up_backend.get_user_list().json_bytes()
	start_response('200 OK', [('Content-Type', 'application/json')])
	return [result]

def app_psn_channel_suggestions(env, start_response):
	existing_team_and_group_ids = up_backend.get_existing_psn_team_and_group_ids()

	result = []
	team_id = slack_team_id()
	for group in groups_list():
		group_id = group['id']
		group_name = group['name']
		if (team_id,group_id) not in existing_team_and_group_ids:
			result.append({
				'channel_name':group_name,
				'channel_type':'slack_group',
				'slack_team_id':team_id,
				'slack_group_id':group_id})

	start_response('200 OK', [('Content-Type', 'application/json')])
	return [json_bytes({'psn_channel_suggestions':result}, schema.psn_channel_suggestions_response)]

def app_psn_list(env, start_response):
	result = up_backend.get_psn_list()

	start_response('200 OK', [('Content-Type', 'application/json')])
	return [json_bytes({'psns':result}, schema.psn_list_response)]

def app_psn_add(env, start_response):
	req = read_json_input(env['wsgi.input'], schema.psn_add_request)
	if req['channel']['channel_type'] != 'slack_group':
		raise ValueError('slack_group is currently the only supported channel_type')

	if req['channel']['slack_team_id'] != slack_team_id():
		raise ValueError('wrong slack_team_id for the PSN that we\'re adding')

	psn_id = up_backend.add_psn(req['psn_name'], req['channel']['slack_team_id'], req['channel']['slack_group_id'])

	start_response('200 OK', [('Content-Type', 'application/json')])
	return [json_bytes({'psn_id':psn_id}, schema.psn_add_response)]

