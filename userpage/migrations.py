def migrations(schema):
	schema.create("users", """(
		user_id SERIAL PRIMARY KEY,
		ultimate_admin BOOLEAN NOT NULL,
		logout_date TIMESTAMP WITH TIME ZONE,
		name VARCHAR NOT NULL,
		join_date TIMESTAMP WITH TIME ZONE NOT NULL)""")
