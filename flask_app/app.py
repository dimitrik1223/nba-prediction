# #pylint: disable=wrong-import-position
import os
import pickle
import pandas as pd
os.environ['KMP_DUPLICATE_LIB_OK']='True'
from machine_learning.nn_regressor import predict, get_predicted_mvp
from flask import Flask, request, render_template, redirect, url_for
from .utils import get_conn, query_db

app = Flask(__name__)
psql_config = {
	"host": "localhost",
	"database": "flask_db",
	"user": os.getenv('DB_USERNAME'),
	"password": os.getenv('DB_PASSWORD'),
}
global conn
conn = get_conn(psql_config)
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
predictors = query_db(conn, "SELECT * FROM mvp_predictors")
stats = query_db(conn, "SELECT * FROM all_stats")
cols_res = query_db(conn,
	"""
	SELECT column_name FROM information_schema.columns
	WHERE table_name = 'all_stats'
	ORDER BY ordinal_position
	"""
)
cols = [col[0] for col in cols_res]
stats_df = pd.DataFrame(stats, columns=cols)

@app.route('/index/', methods=["GET", "POST"])
def index():
	"""
	Render home page.
	"""
	if request.method == "POST" and request.path == "/index/":
		print("Running")
		season = request.form["season"]
		return redirect(url_for("predict_mvp", season=season))
	return render_template("index/index.html", nba_seasons=nba_seasons)

def get_data(season, year_season_map=year_season_map, predictors=predictors, stats_df=stats_df, data_retrieved=False):
	while data_retrieved == False:
		with open("mvp_model.pkl", "rb") as file:
			model = pickle.load(file)
		preds = predict(model=model, data=predictors)
		year = year_season_map[season]
		mvp_res = get_predicted_mvp(data=stats_df, preds=preds, year=year)
		data_retrieved = True
	return year, mvp_res

@app.route('/index/prediction/<season>', methods=["GET", "POST"])
def predict_mvp(season):
	year, mvp_res = get_data(season)
	key_stats = ['"PTS"','"AST"','"TRB"','"3P"','"FT"','"TOV"','"BLK"','"STL"','"G"','"MP"']
	mvp_pred = mvp_res["mvp_pred"]
	if "'" in mvp_pred:
		esc_char_ind = mvp_pred.index("'")
		mvp_pred = mvp_pred[:esc_char_ind] + "\\" + mvp_pred[esc_char_ind:]
	mvp_pred_res = query_db(conn, 
		f"""
		SELECT
			{",".join(key_stats)}
		FROM all_stats
		WHERE "Player" = E'{mvp_pred}'
		AND "Year" = {year}
		"""
	)
	mvp_pred_sts = pd.DataFrame(mvp_pred_res, columns=[col.strip('"') for col in key_stats])
	if request.method == "POST":
		return "WIP"
	return render_template(
		"mvp/index.html", 
		season=season,
		**mvp_res,
		mvp_stats=mvp_pred_sts.to_html(classes="data_table", index=False)
	)	

if __name__ == "__main__":
	app.run(host="0.0.0.0")
