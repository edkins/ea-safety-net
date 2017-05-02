def migrations(schema):
	schema.create("users", """(
		user_id SERIAL PRIMARY KEY,
		ultimate_admin BOOLEAN NOT NULL,
		logout_date TIMESTAMP WITH TIME ZONE,
		name VARCHAR NOT NULL,
		join_date TIMESTAMP WITH TIME ZONE NOT NULL)""")
	schema.create("slack_user", """(
		slack_team_id VARCHAR NOT NULL,
		slack_user_id VARCHAR NOT NULL,
		slack_user_name VARCHAR NOT NULL,
		user_id INTEGER NOT NULL,
		PRIMARY KEY(slack_team_id, slack_user_id))""")
	schema.create("psn", """(
		psn_id SERIAL PRIMARY KEY,
		psn_name VARCHAR NOT NULL,
		slack_team_id VARCHAR NOT NULL,
		slack_group_id VARCHAR NOT NULL,
		creation_date TIMESTAMP WITH TIME ZONE,
		UNIQUE(slack_team_id, slack_group_id))""")
