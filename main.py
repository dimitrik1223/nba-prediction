import os
import pickle
os.environ['KMP_DUPLICATE_LIB_OK']='True'
#pylint: disable=wrong-import-position
from nba_stats_scraping.nba_stats_scraper import Nba_stats_scraper
from nba_stats_scraping.stats_cleaning import clean_data, create_stats_basetable
from machine_learning.nn_regressor import train_model, predict, get_predicted_mvp
from db.db_loader import load_db


def main(postgres_config, year_start=2022, year_end=2024) -> None:
	"""
	Scrape statistics, train model and get predictions.
	"""
	scraper = Nba_stats_scraper(year_start, year_end)
	mvp_stats = scraper.scrape_mvp_stats()
	per_game_stats = scraper.scrape_per_game_stats()
	team_standings = scraper.scrape_team_standings()
	mvp_stats, per_game_stats, team_standings = clean_data(
		mvp_stats, per_game_stats, team_standings
	)
	all_stats = create_stats_basetable(mvp_stats, per_game_stats, team_standings)
	predictors = train_model(train_set=all_stats)
	load_db(dfs=predictors, table_names="mvp_predictors", postgres_config=postgres_config)
	with open("flask_app/mvp_model.pkl", "rb") as file:
		model = pickle.load(file)
	preds = predict(model=model, data=predictors)
	get_predicted_mvp(data=all_stats, preds=preds, year=2022)

if __name__ == "__main__":
	config = {
		"username": os.getenv("POSTGRES_USERNAME"),
		"password": os.getenv("POSTGRES_PASSWORD"),
		"database": os.getenv("POSTGRES_DATABASE")
	}
	main(config)
