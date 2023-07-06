# #pylint: disable=wrong-import-position
import os
import pickle
import pandas as pd
os.environ['KMP_DUPLICATE_LIB_OK']='True'
from machine_learning.nn_regressor import predict, get_predicted_mvp
from flask import Flask, request, render_template
from .utils import get_conn, query_db

app = Flask(__name__)

psql_config = {
	"host": "localhost",
	"database": "flask_db",
	"user": os.getenv('DB_USERNAME'),
	"password": os.getenv('DB_PASSWORD'),
}

@app.route('/', methods=["GET", "POST"])
def home():
	"""
	Render home page.
	"""
	conn = get_conn(psql_config)
	predictors = query_db(conn, "SELECT * FROM mvp_predictors")
	all_stats = query_db(conn, "SELECT * FROM all_stats")
	cols = query_db(conn,
		"""
		SELECT column_name FROM information_schema.columns
		WHERE table_name = 'all_stats'
		ORDER BY ordinal_position
		"""
	)
	col_names = [col[0] for col in cols]
	print(col_names)
	all_stats_df = pd.DataFrame(all_stats, columns=col_names
	)
	years = query_db(conn,
		"""
		SELECT
			MIN("Year") as first_year,
			MAX("Year") as last_year
		FROM all_stats
		"""
	)
	first_year, last_year = years[0][0], years[0][1]
	years = range(first_year, (last_year + 1))
	nba_seasons = [f"{str(year - 1)}-{str(year)}" for year in years]
	year_season_map = dict(zip(nba_seasons, years))
	if request.method == "POST":
		with open("mvp_model.pkl", "rb") as file:
			model = pickle.load(file)
		preds = predict(model=model, data=predictors)
		season = request.form["season"]
		year = year_season_map[season]
		mvp_results = get_predicted_mvp(data=all_stats_df, preds=preds, year=year)
		return render_template("mvp/index.jinja", season=season, **mvp_results)
	return render_template("home/index.jinja", nba_seasons=nba_seasons)

@app.route('/predict/mvp', methods=["GET", "POST"])
def predict_mvp(mvp: str):
	return mvp

if __name__ == "__main__":
	app.run(host="0.0.0.0")
