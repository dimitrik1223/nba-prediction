import os
import time
import requests
import pandas as pd
import logging
import asyncio

from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError

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

	def file_writer(self, dir_name, year, response, target_directory=None):
		"""
		Write HTML files to directory
		"""
		if target_directory is None:
			target_directory = Path.cwd()/"desktop"/"nba_mvp_predictor"
		else:
			target_directory = Path(target_directory)
		
		target_directory = target_directory / dir_name
		target_directory.mkdir(parents=True, exist_ok=True)

		file_path = target_directory / f"{year}.html"
		with open(file_path, "w+") as file:
			file.write(response.text)		
		# Read and return the content of the file
		with open(file_path) as file:
			page = file.read()

		return page

	async def grab_url_html(url, selector, sleep=100, retries=3):
		"""
		Uses Playwright Chromium browser to open URL and grab inner HMTL asynchronously. 
		"""
		html = None
		# Exponential backoff
		for i in range(1, retries+1):
			if i == 1:
				sleep_dur = 10
				time.sleep(sleep_dur)
			else:
				sleep_dur = sleep ** i
				time.sleep(sleep_dur)
			print(f"ZzZ... slept for {sleep_dur} seconds")

			try:
				async with async_playwright() as play:
					browser = await play.chromium.launch()
					page = await browser.new_page()
					await page.goto(url)
					logging.info("URL for %s", await page.title())
					html = await page.inner_hmtl(selector)
			except TimeoutError:
				logging.error("Timeout error on %s", url)
				continue
			else:
				break
		
		return html
			

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
