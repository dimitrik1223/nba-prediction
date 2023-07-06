import psycopg2

def get_conn(config: dict):
	"""
	Create PostgreSQL connection
	"""
	conn = psycopg2.connect(
		**config
	)

	return conn

def query_db(conn, query: str):
	"""
	Create cursor and execute query against db
	"""
	cur = conn.cursor()
	cur.execute(query)
	res = cur.fetchall()

	return res
