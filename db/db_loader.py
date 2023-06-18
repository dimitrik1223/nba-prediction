import os
import logging

from .utils import create_conn, write_table

def load_db(dfs, table_names, postgres_config):
	db = create_conn(**postgres_config)
	conn = db.connect()
	write_table(conn, dfs, table_names)
	conn.close()



