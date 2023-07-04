import os
import pandas as pd
import pickle
os.environ['KMP_DUPLICATE_LIB_OK']='True'
# #pylint: disable=wrong-import-position
# from nba_stats_scraping.nba_stats_scraper import Nba_stats_scraper
# from nba_stats_scraping.stats_cleaning import clean_data, create_stats_basetable
from machine_learning.nn_regressor import train_model, predict, get_predicted_mvp
# from db.db_loader import load_db
from flask import Flask, request, render_template
import psycopg2

app = Flask(__name__)

@app.route('/', methods=["GET", "POST"])
def predict_mvp():
	conn = psycopg2.connect(
		host="localhost",
		database="flask_db",
		user=os.getenv('DB_USERNAME'),
		password=os.getenv('DB_PASSWORD'))
	
	cur = conn.cursor()
	cur.execute("SELECT * FROM mvp_predictors")
	predictors = cur.fetchall()
	cur.execute("SELECT * FROM all_stats")
	all_stats = cur.fetchall()
	all_stats_df = pd.DataFrame(all_stats, columns=[
		'Player', 'Year', 'Pts Won', 'Pts Max', 'Share', 'Pos', 'Age', 'Team',
		'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA',
		'2P%', 'eFG%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL',
		'BLK', 'TOV', 'PF', 'PTS', 'W', 'L', 'W/L%', 'GB', 'PS/G', 'PA/G',
		'SRS', 'Conference'
		]
	)
	cur.execute("""
	SELECT
		MIN("Year") as first_year, 
		MAX("Year") as last_year
	FROM all_stats
	""")
	years = cur.fetchall()
	first_year, last_year = years[0][0], years[0][1]
	years = range(first_year, (last_year + 1))
	print(years)
	nba_seasons = [f"{str(year - 1)}-{str(year)}" for year in years]
	year_season_map = dict(zip(nba_seasons, years))
	with open("mvp_model.pkl", "rb") as file:
		model = pickle.load(file)
	preds = predict(model=model, data=predictors)
	if request.method == "POST":
		season = request.form["season"]
		year = year_season_map[season]
		mvp_announcement = get_predicted_mvp(data=all_stats_df, preds=preds, year=year)
		return mvp_announcement
	return render_template("mvp_predictor/index.jinja", nba_seasons=nba_seasons)

if __name__ == "__main__":
	app.run(host="0.0.0.0")
