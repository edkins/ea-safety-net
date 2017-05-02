import up_backend

from up_slack_kb import groups_list
from up_slack_kb import slack_team_id
from up_conf import json_bytes
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
