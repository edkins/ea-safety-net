from beaker.middleware import SessionMiddleware
import selector

from up_conf import schema
from up_conf import userpage_conf
import up_backend

from up_session import valid_session
from up_session import admin_session
from up_session import app_slackauth
from up_session import app_logout


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

def app_user_list(env, start_response):
	result = up_backend.get_user_list().json_bytes()
	start_response('200 OK', [('Content-Type', 'application/json')])
	return [result]

app = selector.Selector()
app.add('/userpage/slackauth', GET=app_slackauth)
app.add('/userpage/logout', POST=valid_session(app_logout))
app.add('/userpage/privs', GET=valid_session(app_privs))
app.add('/userpage/profile', GET=valid_session(app_profile))
app.add('/userpage/user', GET=admin_session(app_user_list))

beaker_config = {'session.key':'id','session.type':'file','session.data_dir':'/var/easn/userpage/beaker','session.cookie_expires':'true','session.secure':'true'}

application = SessionMiddleware(app, beaker_config)
