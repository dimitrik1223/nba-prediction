import logging
import time

from sqlalchemy import create_engine

def create_conn(username, password, database):
	db = create_engine(f"postgresql://{username}:{password}@localhost:5432/{database}")
	return db

def write_table(conn, dfs, table_names):
	logging.basicConfig(level=logging.INFO)
	try:
		dfs = [dfs]
		table_names = [table_names]
	except:
		raise Exception("DataFrames and data table names need to be passed as lists")

	for index, df in enumerate(dfs):
		start = time.time()
		table_name = table_names[index]
		df.to_sql(table_name, conn, if_exists="replace",index=False)
		end = time.time()
		duration = round(end - start)
		logging.info(f"Table {table_name} loaded in: {duration} seconds")
