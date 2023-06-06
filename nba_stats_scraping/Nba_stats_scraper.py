import requests
import os
import pandas as pd
import shutil

from bs4 import BeautifulSoup

class Nba_stats_scraper:

  def __init__(self, year_start, year_end):
    self.year_start = year_start
    self.year_end = year_end
    self.years = list(range(self.year_start, self.year_end))
    
  def file_writer(self, dir_name, year, data):
    cwd = os.getcwd()
    if not os.path.isdir(f"{cwd}/{dir_name}/"):
        os.mkdir(f"{dir_name}/")
    with open(f"{dir_name}/{year}.html", "w+") as file:
        file.write(data.text)
    with open(f"{dir_name}/{year}.html") as file:
        page = file.read()
    
    return page
    
  
  def scrape_mvp_stats(self):
    mvp_dfs = []
    for year in self.years:
      url = f"https://www.basketball-reference.com/awards/awards_{year}.html" 
      try:
        data = requests.get(url)
        data.raise_for_status()
      except requests.exceptions.RequestException as e:
        print(f"Network request error: {e}")
      page = self.file_writer("mvp/", year, data)
      soup = BeautifulSoup(page, "html.parser")
      soup.find('tr', class_="over_header").decompose()
      mvp_table = soup.find_all(id="mvp")
      mvp_df = pd.read_html(str(mvp_table))[0]
      mvp_df["Year"] = year
      mvp_dfs.append(mvp_df)
    mvp_stats = pd.concat(mvp_dfs).reset_index(drop=True)

    return mvp_stats

  def scrape_per_game_stats(self):
    per_game_stats_dfs = []
    for year in self.years:
      url_start = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
      try:
        data = requests.get(url_start)
        data.raise_for_status()
      except requests.exceptions.RequestException as e:
        print(f"Network request error: {e}")
      page = self.file_writer("player_stats/", year, data)
      soup = BeautifulSoup(page, "html.parser")
      per_game_stats = soup.find_all(id="per_game_stats")
      per_game_stats = pd.read_html(str(per_game_stats))[0]
      per_game_stats["year"] = year
      per_game_stats_dfs.append(per_game_stats)
    past_per_game_stats = pd.concat(per_game_stats_dfs).reset_index(drop=True)

    return past_per_game_stats

  def scrape_team_standings(self):
    team_standings = []
    for year in self.years:
      team_url = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
      try:
        data = requests.get(team_url)
        data.raise_for_status()
      except requests.exceptions.RequestException as e:
        print(f"Network request error: {e}")
      page = self.file_writer("team_standings/", year, data)
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
    