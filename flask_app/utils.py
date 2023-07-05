import os
import psycopg2

def get_conn(kwargs: dict):
	conn = psycopg2.connect(
		**kwargs
	)
	
	return(conn) 

def query_db(conn, query: str):
	cur = conn.cursor()
	cur.execute(query)
	res = cur.fetchall()

	return res