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

def fetch_all_mvps(conn, year_start=1980, year_end=2023):
	res = query_db(conn,
		f"""
		WITH max_pts_year AS (
			select "Year", max("Pts Won") as max_pts from all_stats group by 1
		),
		mvps AS (
			
			SELECT DISTINCT
				all_stats."Player"

			FROM all_stats 
			
			LEFT JOIN max_pts_year 
				ON all_stats."Year" = max_pts_year."Year" 
			
			WHERE all_stats."Pts Won" = max_pts_year."max_pts"
			AND all_stats."Year" >= {year_start}
			AND all_stats."Year" <= {year_end}
		)

		SELECT * FROM mvps;
		"""
	)
	# Extract names from tuples returned
	mvps = [tup[0] for tup in res]

	return mvps
