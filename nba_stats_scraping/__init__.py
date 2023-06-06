from nba_stats_scraping.Nba_stats_scraper import Nba_stats_scraper

def run(year_start, year_end):
	scraper = Nba_stats_scraper(year_start, year_end)
	mvp_stats = scraper.scrape_mvp_stats()
	per_game_stats = scraper.scrape_per_game_stats()
	team_standings = scraper.scrape_team_standings()
	print(team_standings.head())

