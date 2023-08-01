import time
import pandas as pd
import logging
import asyncio
import aiohttp
import pathlib as Path

from bs4 import BeautifulSoup, Comment
from .utils import fetch_paths, retry_request, file_writer

async def grab_url_html(session, url, selector, sleep=5, retries=3):
	"""
	Async coroutine function for parsing HTML element from
	given url. Designed to be used with aiohttp a async
	HTTP client.
	"""
	for i in range(1, retries + 1):
		# Exponential backoff
		sleep_dur = sleep ** i
		time.sleep(sleep_dur)
		print(f"ZzZ... slept for {sleep_dur} seconds")
		try:
			async with session.get(url) as response:
				html = await response.text()
				soup = BeautifulSoup(html, "html.parser")
				parsed_html =  soup.select(selector)
				return parsed_html
		except:
			# Replace with error behaviour
			print("HTTP Error")
			continue

async def scrape_schedule_urls(session, year):
	# Fetch filter elements containing URLs to game schedules per month
	url = f"https://www.basketball-reference.com/leagues/NBA_{year}_games.html"

	return await grab_url_html(session, url, "#content .filter a")

async def scrape_schedules(year_start, year_end):
	box_score_urls = []
	async with aiohttp.ClientSession() as session:
		tasks = []
		for year in range(year_start, year_end + 1):
			tasks.append(scrape_schedule_urls(session, year))

		# Fetch monthly schedule URLs concurrently
		month_urls_list = await asyncio.gather(*tasks)
		for month_url in month_urls_list:
			for a in month_url:
				month = a["href"].split('_')[2].split('-')[1].split('.')[0]
				season_end = int(a["href"].split('_')[1])
				season_start = season_end - 1
				season = f"{season_start}_{season_end}"
				url = f"https://www.basketball-reference.com{a['href']}" 
				schedule_table = await grab_url_html(session, url, "#all_schedule")
				file_writer(f"schedules/{season}_schedule", month, schedule_table, parsed=True)
		logging.info("Done scraping season schedules")
			
		return box_score_urls

def uncomment_html(soup, id):
	"""
	Convert comment block containing HTML to parsable HTML.
	"""
	for comment in soup(text=lambda text: isinstance(text, Comment)):
		if id in comment.string:
			tag = BeautifulSoup(comment, "html.parser")
			html_str = str(comment.replace_with(tag))
			html = BeautifulSoup(html_str, "html.parser")
			return html
	return soup

def extract_team_abr(soup):
	"""
	Extract team abreviations from parsed boxscores page HTML
	"""
	team_abrs = []
	hyperlinks = soup.find_all("a")
	for link in hyperlinks:
		if "/teams/" in link["href"]:
			team_abr = link["href"].split("/")[2]
			team_abrs.append(team_abr)
			if len(team_abrs) == 2:
				return team_abrs

def parse_html_files(html_ids: list[str], target_dir=None, path_sub_str=None) -> dict:
	"""
	Iterates through directory and parses deserved elements from HTML files. 
	"""
	if not isinstance(html_ids, list):
		raise TypeError("html_ids must be a list of HTML element IDs.")

	table_dict = {}
	dir = fetch_paths(
		is_dir=True,
		target_dir=target_dir,
		contains=path_sub_str
	)
	for item in dir:
		files = fetch_paths(target_dir=item)
		for path in files:
			dfs = []
			with open(path, "r") as file:
				html = file.read()
				soup = BeautifulSoup(html, "html.parser")
				# Add HTML team stat table ids dynamically
				if "boxscores" in path:
					team_abrs = extract_team_abr(soup)
					team_stat_ids = [f"box-{team_abr}-game-basic" for team_abr in team_abrs]
					for id in team_stat_ids:
						html_ids.append(id)
				for id in html_ids:
					uncomm_soup = uncomment_html(soup, id)
					table = uncomm_soup.find_all(id=f"{id}")
					table_df = pd.read_html(str(table))
					dfs.append(table_df)
					table_dict[f"{id}"] = dfs
				# Remove added HTML team stat table ids
				if team_stat_ids:
					for id in team_stat_ids:
						html_ids.remove(id)

	for key, value in table_dict.items():
		table_dict[key] = pd.concat(value).reset_index(drop=True)

	return table_dict

async def scrape_box_scores():
	schedule_dirs = fetch_paths(True, "schedule")
	for dir in schedule_dirs:
		season_sch_dir = Path(dir)
		for item in season_sch_dir.iterdir():
			with open(item, "r") as file:
				monthly_schedule = file.read()
				soup = BeautifulSoup(monthly_schedule, "html.parser")
				for a in soup.find_all("a"):
					url = a["href"]
					if url.startswith("/boxscores/") and url.endswith(".html"):
						box_score_url = f"https://www.basketball-reference.com{url}"
						async with aiohttp.ClientSession() as session:
							box_score_page = await grab_url_html(session, box_score_url, "#content")
							file_name = box_score_url.split('/')[4].split(".")[0]
							season_end = int(file_name[0:4])
							season_start = season_end - 1
							file_writer(
								dir_name=f"boxscores/{season_start}_{season_end}_boxscores", 
								file_name=file_name,
								response=box_score_page, 
								parsed=True
							)
		logging.info("Box scores scraped and stored")

class Nba_stats_scraper:
	"""
	basketball-references.com scraping class
	"""

	def __init__(self, year_start, year_end):
		self.year_start = year_start
		self.year_end = year_end
		self.years = list(range(self.year_start, self.year_end))

	def scrape_mvp_stats(self):
		"""
		Scrape dataset of historical MVP award voting statistics
		"""
		mvp_dfs = []
		for year in self.years:
			url = f"https://www.basketball-reference.com/awards/awards_{year}.html"
			response = retry_request(url, max_retries=3)
			time.sleep(5)
			page = file_writer("nba_stats_scraping/mvp/", year, response)
			soup = BeautifulSoup(page, "html.parser")
			soup.find('tr', class_="over_header").decompose()
			mvp_table = soup.find_all(id="mvp")
			mvp_df = pd.read_html(str(mvp_table))[0]
			mvp_df["Year"] = year
			mvp_dfs.append(mvp_df)
		mvp_stats = pd.concat(mvp_dfs).reset_index(drop=True)

		return mvp_stats

	def scrape_per_game_stats(self):
		"""
		Scrape historical dataset of player per game statistics
		"""
		per_game_stats_dfs = []
		for year in self.years:
			url = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
			response = retry_request(url, max_retries=3)
			time.sleep(5)
			page = file_writer("nba_stats_scraping/player_stats/", year, response)
			soup = BeautifulSoup(page, "html.parser")
			per_game_stats = soup.find_all(id="per_game_stats")
			per_game_stats = pd.read_html(str(per_game_stats))[0]
			per_game_stats["Year"] = year
			per_game_stats_dfs.append(per_game_stats)
		past_per_game_stats = pd.concat(per_game_stats_dfs).reset_index(drop=True)

		return past_per_game_stats

	def scrape_team_standings(self):
		"""
		Scrape historical dataset of team standings statistics
		"""
		team_standings = []
		for year in self.years:
			url = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
			response = retry_request(url, max_retries=3)
			time.sleep(5)
			page = file_writer("nba_stats_scraping/team_standings/", year, response)
			soup = BeautifulSoup(page, "html.parser")
			for header in soup.find_all("tr", class_="thead"):
				header.decompose()
			team_standings_e = soup.find(id="divs_standings_E")
			team_standings_w = soup.find(id="divs_standings_W")
			df_standings_e = pd.read_html(str(team_standings_e))[0]
			df_standings_w = pd.read_html(str(team_standings_w))[0]
			df_standings_e.rename(columns={"Eastern Conference": "Team"}, inplace=True)
			df_standings_e["Conference"] = "Eastern"
			df_standings_w.rename(columns={"Western Conference": "Team"}, inplace=True)
			df_standings_w["Conference"] = "Western"
			df_standings_all = pd.concat([df_standings_e, df_standings_w])
			df_standings_all["Year"] = year
			team_standings.append(df_standings_all)
		all_team_standings = pd.concat(team_standings)

		return all_team_standings
