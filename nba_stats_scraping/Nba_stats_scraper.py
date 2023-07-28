import os
import time
import requests
import pandas as pd
import logging
import asyncio
import aiohttp

from pathlib import Path
from bs4 import BeautifulSoup

class Nba_stats_scraper:
	"""
	basketball-references.com scraping class
	"""

	def __init__(self, year_start, year_end):
		self.year_start = year_start
		self.year_end = year_end
		self.years = list(range(self.year_start, self.year_end))

	def make_request(self, url):
		"""
		Make get request to basketball-references.com
		"""
		try:
			response = requests.get(url)
			if response.status_code == 429:
				raise requests.exceptions.HTTPError("Rate limit exceeded")
			response.raise_for_status()
			return response
		except requests.exceptions.RequestException as e:
			print(f"Network request error: {e}")
			return None

	def retry_request(self, url, max_retries=3):
		"""
		Retry on get requests
		"""
		retries = 0
		while retries < max_retries:
			response = self.make_request(url)
			if response.status_code == 429:
				retries += 1
				sleep_duration = int(response.headers.get("Retry-After", 1))
				print(f"Retrying after {sleep_duration} seconds")
				time.sleep(sleep_duration)
			else:
				return response

	def file_writer(self, dir_name, file_name, response, target_directory=None, parsed=False):
		"""
		Write HTML files to directory
		"""
		if target_directory is None:
			target_directory = Path.cwd()/"desktop"/"nba_mvp_predictor"
		else:
			target_directory = Path(target_directory)
		
		target_directory = target_directory / dir_name
		target_directory.mkdir(parents=True, exist_ok=True)

		file_path = target_directory / f"{file_name}.html"
		with open(file_path, "w+") as file:
			if parsed:
				file.write(str(response))
			else:		
				file.write(response.text)		
		# Read and return the content of the file
		with open(file_path) as file:
			page = file.read()

		return page

	async def grab_url_html(self, session, url, selector, sleep=5, retries=3):
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

	async def scrape_schedule_urls(self, session, year):
		# Fetch filter elements containing URLs to game schedules per month
		url = f"https://www.basketball-reference.com/leagues/NBA_{year}_games.html"

		return await self.grab_url_html(session, url, "#content .filter a")

	async def scrape_schedules(self):
		box_score_urls = []
		async with aiohttp.ClientSession() as session:
			tasks = []
			for year in range(self.year_start, self.year_end + 1):
				tasks.append(self.scrape_schedule_urls(session, year))

			# Fetch monthly schedule URLs concurrently
			month_urls_list = await asyncio.gather(*tasks)
			for month_url in month_urls_list:
				print(month_url)
				for a in month_url:
					month = a["href"].split('_')[2].split('-')[1].split('.')[0]
					season_end = int(a["href"].split('_')[1])
					season_start = season_end - 1
					season = f"{season_start}_{season_end}"
					url = f"https://www.basketball-reference.com{a['href']}" 
					schedule_table = await self.grab_url_html(session, url, "#all_schedule")
					self.file_writer(f"{season}_schedule", month, schedule_table, parsed=True)
			logging.info("Done scraping season schedules")
			
			return box_score_urls

	async def scrape_box_scores(self):
		dir = Path(f"{Path.cwd()}/desktop/nba_mvp_predictor/")
		schedule_dirs = [
			dir.as_posix() for dir in dir.iterdir() 
			if dir.is_dir() and "schedule" in dir.as_posix()
		]
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
								box_score_page = await self.grab_url_html(session, box_score_url, "#content")
								file_name = box_score_url.split('/')[4].split(".")[0]
								year = file_name[0:4]
								self.file_writer(
									dir_name="box_scores", 
									file_name=file_name, 
									response=box_score_page, 
									parsed=True
								)
		logging.info("Box scores scraped and stored")

	def scrape_mvp_stats(self):
		"""
		Scrape dataset of historical MVP award voting statistics
		"""
		mvp_dfs = []
		for year in self.years:
			url = f"https://www.basketball-reference.com/awards/awards_{year}.html"
			response = self.retry_request(url, max_retries=3)
			time.sleep(5)
			page = self.file_writer("nba_stats_scraping/mvp/", year, response)
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
			response = self.retry_request(url, max_retries=3)
			time.sleep(5)
			page = self.file_writer("nba_stats_scraping/player_stats/", year, response)
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
			response = self.retry_request(url, max_retries=3)
			time.sleep(5)
			page = self.file_writer("nba_stats_scraping/team_standings/", year, response)
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
