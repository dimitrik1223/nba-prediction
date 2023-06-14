import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

from nba_stats_scraping.nba_stats_scraper import Nba_stats_scraper
from nba_stats_scraping.stats_cleaning import clean_data, create_stats_basetable
from machine_learning.nn_regressor import train_nn

def main(year_start, year_end):
	scraper = Nba_stats_scraper(year_start, year_end)
	mvp_stats = scraper.scrape_mvp_stats()
	per_game_stats = scraper.scrape_per_game_stats()
	team_standings = scraper.scrape_team_standings()
	mvp_stats, per_game_stats, team_standings = clean_data(
		mvp_stats, per_game_stats, team_standings
	)
	all_stats = create_stats_basetable(mvp_stats, per_game_stats, team_standings)
	train_nn(all_stats)

if __name__ == "__main__":
	main(year_start=2004, year_end=2024)
