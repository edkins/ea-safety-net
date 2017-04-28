import psycopg2 as dbapi2
from up_conf import userpage_conf

class SchemaError(Exception):
	pass

class WeirdStateError(Exception):
	pass

class Schema:
	def __init__(self, db):
		self.db = db
		self.current_versions = {}
		self.versions = {}

		cur = self.db.cursor()
		try:
			cur.execute('CREATE TABLE IF NOT EXISTS table_schema(table_name VARCHAR PRIMARY KEY, version INTEGER NOT NULL)')
			self.db.commit()
		finally:
			cur.close()

		cur = self.db.cursor()
		try:
			cur.execute('SELECT table_name, version FROM table_schema')
			for (table_name,version) in cur.fetchall():
				if not isinstance(table_name, str):
					raise WeirdStateError('Table name is not a string: %s' % (table_name,))
				if not isinstance(version, int):
					raise WeirdStateError('Version is not an int: %s for table %s' % (version,table_name))
				if table_name in self.versions:
					raise WeirdStateError('Already encountered table name: %s' % (table_name,))
				if version < 1:
					raise WeirdStateError('Version is less than 1: %s for table %s' % (version, table_name))
				self.current_versions[table_name] = version
				print('Table %s was at version %s' % (table_name, version))
			print('---')
		finally:
			cur.close()

	def _new_stuff(self):
		have_newer = False
		have_older = False
		for table_name in self.current_versions:
			if table_name not in self.versions or self.versions[table_name] < self.current_versions[table_name]:
				have_older = True

		for table_name in self.versions:
			if table_name not in self.current_versions or self.current_versions[table_name] < self.versions[table_name]:
				have_newer = True

		if have_older and have_newer:
			raise WeirdStateError('Some version numbers have gone up and some have gone down')

		return have_newer

	def _execute_version_number_updates(self, cur):
		for table_name in self.versions:
			version = self.versions[table_name]
			if table_name not in self.current_versions:
				cur.execute('INSERT INTO table_schema(table_name,version) VALUES (%s,%s)', (table_name, version))
			elif self.current_versions[table_name] < version:
				cur.execute('UPDATE table_schema SET version=%s WHERE table_name=%s', (version, table_name))

	def create(self, table_name, columns):
		if table_name in self.versions:
			raise SchemaError('Table already exists: %s' % table_name)
		version = 1
		self.versions[table_name] = version
		
		if self._new_stuff():
			view_name = '%s_%03d' % (table_name, version)
			print(view_name)
			sql_create = 'CREATE TABLE %s %s' % (table_name, columns)
			sql_view = 'CREATE VIEW %s AS SELECT * FROM %s' % (view_name, table_name)
			cur = self.db.cursor()
			try:
				print(sql_create)
				cur.execute(sql_create)
				print(sql_view)
				cur.execute(sql_view)
				self._execute_version_number_updates(cur)
				self.db.commit()
			finally:
				cur.close()
			self.current_versions = dict(self.versions)
			print('---')

def db_for_migration():
	db_host = userpage_conf['db_host']
	db_port = userpage_conf['db_port']
	db_name = userpage_conf['db_name']
	db_user = userpage_conf['db_migration_user']
	db_password = userpage_conf['db_migration_password']
	return dbapi2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)

