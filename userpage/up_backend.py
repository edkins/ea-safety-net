from up_conf import userpage_conf
from up_conf import schema
from up_conf import json_bytes
import sql_helper

class WeirdStateError(Exception):
	pass

class AuthError(Exception):
	pass

class UserPageDB:
	def __init__(self):
		self.db = sql_helper.db_for_app()

	def find_slack_user(self, slack_team_id, slack_user_id):
		""" Return the user_id as a string if a slack user is known, otherwise return None."""
		if not isinstance(slack_team_id, str):
			raise ValueError('slack_team_id must be a string, was %s' % (slack_team_id,))
		if not isinstance(slack_user_id, str):
			raise ValueError('slack_team_id must be a string, was %s' % (slack_user_id,))

		cur = self.db.cursor()
		try:
			sql = 'SELECT user_id FROM slack_user_001 WHERE slack_team_id = %s AND slack_user_id = %s'
			cur.execute(sql, (slack_team_id, slack_user_id))
			results = cur.fetchall()
			if len(results) == 0:
				return None
			elif len(results) == 1:
				return str(results[0][0])
			else:
				raise WeirdStateError('Multiple users returned from slack_user which doesn\'t make sense because that should have been a primary key')
		finally:
			cur.close()

	def add_new_user_from_slack(self, slack_team_id, slack_user_id, slack_user_name, ultimate_admin):
		"""
		Adds a new user to the users and slack_user tables. Returns the new user_id
		"""
		cur = self.db.cursor()
		try:
			cur.execute("SELECT NEXTVAL('users_user_id_seq')")
			user_id = cur.fetchone()[0]
			cur.execute("INSERT INTO users(user_id, ultimate_admin, logout_date, name, join_date) VALUES (%s, %s, NULL, %s, NOW())", (user_id, ultimate_admin, slack_user_name))
			cur.execute("INSERT INTO slack_user(slack_team_id, slack_user_id, slack_user_name, user_id) VALUES (%s, %s, %s, %s)", (slack_team_id, slack_user_id, slack_user_name, user_id))
			self.db.commit()
			return str(user_id)
		finally:
			cur.close()

	def user_privileges(self, user_id):
		if not isinstance(user_id, str):
			raise ValueError('user_id must be a string, was %s' % (user_id,))

		cur = self.db.cursor()
		try:
			cur.execute("SELECT ultimate_admin FROM users_001 WHERE user_id = %s", (int(user_id),))
			results = cur.fetchall()
			if len(results) == 0:
				raise AuthError('User not found: %s' % (user_id,))
			elif len(results) == 1:
				return (results[0][0],)
			else:
				raise WeirdStateError('Multiple users returned which doesn\'t make sense because that should have been a primary key')
		finally:
			cur.close()

	def user_profile(self, user_id):
		if not isinstance(user_id, str):
			raise ValueError('user_id must be a string, was %s' % (user_id,))

		cur = self.db.cursor()
		try:
			cur.execute("SELECT name FROM users_001 WHERE user_id = %s", (int(user_id),))
			results = cur.fetchall()
			if len(results) == 0:
				raise AuthError('User not found: %s' % (user_id,))
			elif len(results) == 1:
				return (results[0][0],)
			else:
				raise WeirdStateError('Multiple users returned which doesn\'t make sense because that should have been a primary key')
		finally:
			cur.close()

	def user_list(self):
		cur = self.db.cursor()
		try:
			cur.execute("""
				SELECT users_001.user_id, users_001.name, users_001.ultimate_admin,
					slack_user_001.slack_user_id, slack_user_001.slack_team_id
				FROM users_001 LEFT OUTER JOIN slack_user_001
				ON users_001.user_id = slack_user_001.user_id
				""")
			return cur.fetchall()
		finally:
			cur.close()

	def existing_psn_team_and_group_ids(self):
		cur = self.db.cursor()
		try:
			cur.execute("SELECT slack_team_id, slack_group_id FROM psn_001")
			return cur.fetchall()
		finally:
			cur.close()

	def psn_list(self):
		cur = self.db.cursor()
		try:
			cur.execute("SELECT psn_id, psn_name, slack_group_id, slack_team_id, creation_date FROM psn_001")
			return cur.fetchall()
		finally:
			cur.close()

	def add_psn(self, psn_name, slack_team_id, slack_group_id):
		cur = self.db.cursor()
		try:
			cur.execute("SELECT NEXTVAL('psn_psn_id_seq')")
			psn_id = cur.fetchone()[0]
			cur.execute("""INSERT INTO psn(psn_id,psn_name,slack_group_id,slack_team_id,creation_date)
				VALUES (%s,%s,%s,%s,NOW())""", (psn_id,psn_name,slack_group_id,slack_team_id))
			self.db.commit()
			return str(psn_id)
		finally:
			cur.close()

	def close(self):
		self.db.close()

def check_new_slack_user_permissions(slack_team_id, slack_user_id):
	"""
	Check whether policy allows this user to be added from slack.
	Right now it checks that the team_id corresponds to the one specified in the configuration file,
	meaning only a single slack team is supported (and that all users from that team are welcome to
	join this system)

	Additionally, one user gets the ultimate_admin bit set as soon as they join. This is specified
	in the config file as initial_admin_slack_id. This gets returned as a boolean from this function.
	"""
	if not isinstance(slack_team_id, str):
		raise ValueError('slack_team_id must be a string, was %s' % (slack_team_id,))
	if not isinstance(slack_user_id, str):
		raise ValueError('slack_team_id must be a string, was %s' % (slack_user_id,))
	
	if slack_team_id != userpage_conf['team_id']:
		raise AuthError('User tried to join from the wrong slack team. Was %s, should be %s', slack_team_id, userpage_conf['team_id'])

	ultimate_admin = (slack_user_id == userpage_conf['initial_admin_slack_id'])
	return ultimate_admin

def get_or_create_user_id(slack_team_id, slack_user_id, slack_user_name):
	"""
	Returns user_id as a string, or throws an exception if the given slack user is not allowed to access this system
	or there's some other problem.

	A new user will be created if it's somebody we haven't met before, and they belong to the right team.
	"""
	udb = UserPageDB()
	try:
		existing_user_id = udb.find_slack_user(slack_team_id, slack_user_id)
		if existing_user_id != None:
			return existing_user_id 

		ultimate_admin = check_new_slack_user_permissions(slack_team_id, slack_user_id)

		return udb.add_new_user_from_slack(slack_team_id, slack_user_id, slack_user_name, ultimate_admin)
	finally:
		udb.close()

def get_privs(user_id):
	"""
	Returns an object representing a user's privileges. Throws an exception if the user doesn't exist.
	"""
	udb = UserPageDB()
	try:
		(admin,) = udb.user_privileges(user_id)
		return Privs(admin)
	finally:
		udb.close()

def get_profile(user_id):
	"""
	Returns an object representing a user's profile, including their name. Throws an exception if the user doesn't exist.
	"""
	udb = UserPageDB()
	try:
		(name,) = udb.user_profile(user_id)
		return Profile(name)
	finally:
		udb.close()

def get_user_list():
	"""
	Returns a list of all users
	"""
	udb = UserPageDB()
	try:
		users = udb.user_list()
		return UserList([_transform_user(u) for u in users])
	finally:
		udb.close()

def _transform_user(row):
	return {
		'user_id': str(row[0]),
		'name': row[1],
		'ultimate_admin': row[2],
		'slack_user_id': row[3],
		'slack_team_id': row[4]
	}

def get_existing_psn_team_and_group_ids():
	"""
	Returns a list of team/group id pairs that are in use by existing (non-closed) PSN's.
	This is so that they can be filtered out of the suggestion list.
	"""
	udb = UserPageDB()
	try:
		psns = udb.existing_psn_team_and_group_ids()
		return [(p[0],p[1]) for p in psns]
	finally:
		udb.close()

def get_psn_list():
	"""
	Returns a list of all PSNs
	"""
	udb = UserPageDB()
	try:
		psns = udb.psn_list()
		return [_transform_psn(p) for p in psns]
	finally:
		udb.close()

def _transform_psn(row):
	return {
		'psn_id':row[0],
		'psn_name':row[1],
		'slack_group_id':row[2],
		'slack_team_id':row[3],
		'creation_date':row[4].timestamp()
	}

class Privs:
	def __init__(self, admin):
		self.admin = admin

	def json_bytes(self):
		privs = {'user':{}}
		if self.admin:
			privs['admin'] = {}
		obj = {'privileges':privs}
		return json_bytes(obj, schema.privs_response)

class Profile:
	def __init__(self, name):
		self.name = name

	def json_bytes(self):
		obj = {'profile':{'name':self.name}}
		return json_bytes(obj, schema.profile_response)

class UserList:
	def __init__(self, users):
		self.users = users

	def json_bytes(self):
		obj = {'users':self.users}
		return json_bytes(obj, schema.user_list_response)

def add_psn(psn_name, slack_team_id, slack_group_id):
	"""
	Adds a new PSN and returns its id as a string.
	"""
	udb = UserPageDB()
	try:
		return udb.add_psn(psn_name, slack_team_id, slack_group_id)
	finally:
		udb.close()

