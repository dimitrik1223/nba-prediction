import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

from nba_stats_scraping.nba_stats_scraper import Nba_stats_scraper
from nba_stats_scraping.stats_cleaning import clean_data, create_stats_basetable
from machine_learning.nn_regressor import train_nn
from db.db_loader import load_db


def main(postgres_config, year_start=2022, year_end=2024) -> None:
	scraper = Nba_stats_scraper(year_start, year_end)
	mvp_stats = scraper.scrape_mvp_stats()
	per_game_stats = scraper.scrape_per_game_stats()
	team_standings = scraper.scrape_team_standings()
	mvp_stats, per_game_stats, team_standings = clean_data(
		mvp_stats, per_game_stats, team_standings
	)
	all_stats = create_stats_basetable(mvp_stats, per_game_stats, team_standings)
	load_db(dfs=all_stats, table_names="mvp_stats", postgres_config=postgres_config)
	# train_nn(all_stats)
	

if __name__ == "__main__":
	postgres_config = {
		"username": os.getenv("POSTGRES_USERNAME"),
		"password": os.getenv("POSTGRES_PASSWORD"),
		"database": os.getenv("POSTGRES_DATABASE")
	}
	main(postgres_config)

