import requests
import os
import pandas as pd
import shutil

from bs4 import BeautifulSoup

class Nba_stats_scraper:

  def __init__(self, year_start, year_end):
    self.year_start = year_start
    self.year_end = year_end
    
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
    years = list(range(self.year_start, self.year_end))
    for year in years:
      url = f"https://www.basketball-reference.com/awards/awards_{year}.html" 
      data = requests.get(url)
      page = self.file_writer("mvp/", year, data)
      soup = BeautifulSoup(page, "html.parser")
      soup.find('tr', class_="over_header").decompose()
      mvp_table = soup.find_all(id="mvp")
      mvp_df = pd.read_html(str(mvp_table))[0]
      mvp_df["Year"] = year
      mvp_dfs.append(mvp_df)
    mvp_stats = pd.concat(mvp_dfs).reset_index(drop=True)

    return mvp_stats