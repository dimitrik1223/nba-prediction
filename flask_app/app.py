# #pylint: disable=wrong-import-position
import os
import pickle
import pandas as pd
os.environ['KMP_DUPLICATE_LIB_OK']='True'
from machine_learning.nn_regressor import predict, get_predicted_mvp
from flask import Flask, request, render_template, redirect, url_for
from .utils import get_conn, query_db, fetch_all_mvps

app = Flask(__name__)
PSQL_CONFIG = {
	"host": "localhost",
	"database": "flask_db",
	"user": os.getenv('DB_USERNAME'),
	"password": os.getenv('DB_PASSWORD'),
}
global CONN
CONN = get_conn(PSQL_CONFIG)
years = query_db(CONN,
	"""
	SELECT
		MIN("Year") as first_year,
		MAX("Year") as last_year
	FROM all_stats
	"""
)
FIRST_YEAR, LAST_YEAR = years[0][0], years[0][1]
YEARS = range(FIRST_YEAR, (LAST_YEAR + 1))
NBA_SEASONS = [f"{str(year - 1)}-{str(year)}" for year in YEARS]
YEAR_SEASON_MAP = dict(zip(NBA_SEASONS, YEARS))
PREDICTORS = query_db(CONN, "SELECT * FROM mvp_predictors")
STATS = query_db(CONN, "SELECT * FROM all_stats")
cols_res = query_db(CONN,
	"""
	SELECT column_name FROM information_schema.columns
	WHERE table_name = 'all_stats'
	ORDER BY ordinal_position
	"""
)
COLS = [col[0] for col in cols_res]
STATS_DF = pd.DataFrame(STATS, columns=COLS)


def get_data(season, year_season_map=YEAR_SEASON_MAP, predictors=PREDICTORS, stats_df=STATS_DF, data_retrieved=False):
	while data_retrieved == False:
		with open("mvp_model.pkl", "rb") as file:
			model = pickle.load(file)
		preds = predict(model=model, data=PREDICTORS)
		year = YEAR_SEASON_MAP[season]
		mvp_res = get_predicted_mvp(data=STATS_DF, preds=preds, year=year)
		data_retrieved = True
	return year, mvp_res

@app.route('/index/', methods=["GET", "POST"])
def index():
	"""
	Render home page.
	"""
	if request.method == "POST" and request.path == "/index/":
		season = request.form["season"]
		return redirect(url_for("predict_mvp", season=season))
	return render_template("index/index.html", nba_seasons=NBA_SEASONS)

@app.route('/index/prediction/<season>', methods=["GET", "POST"])
def predict_mvp(season):
	year, mvp_res = get_data(season)
	key_stats = ['"PTS"','"AST"','"TRB"','"3P"','"FT"','"TOV"','"BLK"','"STL"','"G"','"MP"']
	mvp_pred = mvp_res["mvp_pred"]
	mvp_actual = mvp_res["mvp_actual"]
	if "'" in mvp_pred:
		esc_char_ind = mvp_pred.index("'")
		mvp_pred = mvp_pred[:esc_char_ind] + "\\" + mvp_pred[esc_char_ind:]
	mvp_pred_res = query_db(CONN, 
		f"""
		SELECT
			{",".join(key_stats)}
		FROM all_stats
		WHERE "Player" = E'{mvp_pred}'
		AND "Year" = {year}
		"""
	)
	mvp_pred_sts = pd.DataFrame(mvp_pred_res, columns=[col.strip('"') for col in key_stats])
	pred_img_url = "mvp_imgs/" + mvp_pred.lower().replace(" ", "_") + ".jpg"
	actual_img_url = "mvp_imgs/" + mvp_actual.lower().replace("-", " ").replace(" ", "_") + ".jpg"
	all_mvps = fetch_all_mvps(CONN)
	if request.method == "POST":
		if request.form.get("Yes"):
			if mvp_pred == mvp_actual:
				return render_template(
					"mvp/correct_choice.html",
					season=season,
					mvp_actual=mvp_actual,
					actual_img_url=actual_img_url
				)
			else:
				return render_template(
					"mvp/incorrect_choice.html",
					season=season,
					mvp_actual=mvp_actual,
					actual_img_url=actual_img_url
				)
		else:
			if mvp_pred != mvp_actual:
				sec_res = True
				corr_res_val = None
				if request.form.get("corr_res"):
					if mvp_actual == request.form["corr_res"]:
						corr_res_val = True
					else:
						corr_res_val = False
				return render_template(
					"mvp/correct_choice.html", 
					sec_res=sec_res,
					season=season,
					mvp_actual=mvp_actual,
					actual_img_url=actual_img_url,
					corr_res_val=corr_res_val,
					all_mvps=all_mvps
				)
			else:
				return render_template(
					"mvp/incorrect_choice.html",
					season=season,
					mvp_actual=mvp_actual,
					actual_img_url=actual_img_url
				)
	return render_template(
		"mvp/index.html", 
		season=season,
		**mvp_res,
		mvp_stats=mvp_pred_sts.to_html(classes="data_table", index=False),
		pred_img_url=pred_img_url,
		actual_img_url=actual_img_url
	)	

if __name__ == "__main__":
	app.run(host="0.0.0.0")
