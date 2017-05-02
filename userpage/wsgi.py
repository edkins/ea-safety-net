from beaker.middleware import SessionMiddleware
import selector

from up_session import valid_session
from up_session import admin_session
from up_session import app_slackauth
from up_session import app_logout

from up_user import app_privs
from up_user import app_profile
from up_admin import app_user_list
from up_admin import app_psn_list
from up_admin import app_psn_add
from up_admin import app_psn_channel_suggestions

from up_kickbot import app_kickbot

app = selector.Selector()
app.add('/userpage/slackauth', GET=app_slackauth)
app.add('/userpage/logout', POST=valid_session(app_logout))
app.add('/userpage/privs', GET=valid_session(app_privs))
app.add('/userpage/profile', GET=valid_session(app_profile))

app.add('/userpage/user', GET=admin_session(app_user_list))
app.add('/userpage/psn', GET=admin_session(app_psn_list))
app.add('/userpage/psn/add', POST=admin_session(app_psn_add))
app.add('/userpage/suggest/psn_channel', GET=admin_session(app_psn_channel_suggestions))

app.add('/kickbot/slackendpoint', POST=app_kickbot)

beaker_config = {'session.key':'id','session.type':'file','session.data_dir':'/var/easn/userpage/beaker','session.cookie_expires':'true','session.secure':'true'}

application = SessionMiddleware(app, beaker_config)
