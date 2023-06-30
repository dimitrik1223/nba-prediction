import os
import pandas as pd
import pickle
os.environ['KMP_DUPLICATE_LIB_OK']='True'
# #pylint: disable=wrong-import-position
# from nba_stats_scraping.nba_stats_scraper import Nba_stats_scraper
# from nba_stats_scraping.stats_cleaning import clean_data, create_stats_basetable
from machine_learning.nn_regressor import train_model, predict, get_predicted_mvp
# from db.db_loader import load_db
from flask import Flask
import psycopg2

app = Flask(__name__)

@app.route('/')
def main():
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
	with open("mvp_model.pkl", "rb") as file:
		model = pickle.load(file)
	preds = predict(model=model, data=predictors)
	mvp_announcement = get_predicted_mvp(data=all_stats_df, preds=preds, year=1993)

	return mvp_announcement

if __name__ == "__main__":
	main()
