from .utils import create_conn, write_table

def load_db(dfs, table_names, postgres_config) -> None:
	"""
	Writes DataFrames to Postgres database tables if they don't
	already exist in the database.

	args:
	postgres_config (dict): Stores the username, password, and database credentials
	for the Postgres database the tables should be loaded in.
	"""
	postgres_conn = create_conn(**postgres_config)
	conn = postgres_conn.connect()
	write_table(conn, dfs, table_names)
	conn.close()
