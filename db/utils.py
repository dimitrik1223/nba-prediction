import logging
import time

from sqlalchemy import create_engine

def create_conn(username, password, database):
	"""
	Creates connection to Postgres database.

	args:
	username (str): Postgres username
	password (str): Password for Postgres user
	database (str): Postgres database to load

	returns:
	Postgres database connection
	"""
	postgres_conn = create_engine(f"postgresql://{username}:{password}@localhost:5432/{database}")
	return postgres_conn

def write_table(conn, stats_dfs, table_names):
	"""
	Writes tables to Postgres database if they don't already exist

	args:
	dfs (list): DataFrames to write to database
	table_names (list): Names to use for tables loaded
	"""
	logging.basicConfig(level=logging.INFO)
	try:
		stats_dfs = [stats_dfs]
		table_names = [table_names]
	except TypeError as exception:
		raise Exception("DataFrames and data table names need to be passed as lists") from exception

	for index, stats_df in enumerate(stats_dfs):
		start = time.time()
		table_name = table_names[index]
		stats_df.to_sql(table_name, conn, if_exists="replace",index=False)
		end = time.time()
		duration = round(end - start)
		logging.info("Table %s loaded in: %s seconds", table_name, duration)
