from nba_stats_scraping.Nba_stats_scraper import Nba_stats_scraper

def run(year_start, year_end):
	scraper = Nba_stats_scraper(year_start, year_end)
	mvp_stats = scraper.scrape_mvp_stats()
	print(mvp_stats.head())
