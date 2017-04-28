import sql_helper
import migrations

db = sql_helper.db_for_migration()
try:
	schema = sql_helper.Schema(db)
	migrations.migrations(schema)
	print('Data migration complete')
finally:
	db.close()

