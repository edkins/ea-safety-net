from beaker.middleware import SessionMiddleware
import time

def app(env, start_response):
	session = env['beaker.session']

	if session.last_accessed == None or time.time() - session.last_accessed < 5.0:
		if 'counter' in session:
			session['counter'] += 1
		else:
			session['counter'] = 0

		session.save()
		text = "Hello " + str(session['counter'])
	else:
		session.delete()
		text = "I deleted it"

	start_response('200 OK', [('Content-Type', 'text/plain')])

	return [bytes(text,'utf-8')]

application = SessionMiddleware(app, {'session.key':'id','session.type':'file','session.data_dir':'/var/easn/userpage/beaker','session.cookie_expires':'true','session.secure':'true'})
