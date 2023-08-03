import pandas as pd

from datetime import datetime

def extract_total_row(data):
	"""
	Extracts the stat totals row from dataframe of per game player statistcs.
	"""
	if data.shape[0] == 1:
		return data
	team = data.iloc[-1, :]["Team"]
	data = data[data["Team"] == "TOT"]
	data["Team"] = team
	return data

def clean_data(mvp_stats, player_stats, team_stats):
	"""
	Clean each respective dataset
	"""
	mvp_stats = mvp_stats[["Player", "Year", "Pts Won", "Pts Max", "Share"]]
	del player_stats['Rk']

	# Remove asteriks from hall of famers
	player_stats["Player"] = player_stats["Player"].str.replace("*", "", regex=False)
	player_stats.rename(columns={"Tm": "Team"}, inplace=True)
	team_stats["Team"] = team_stats["Team"].str.replace("*", "", regex=False)
	player_stats = player_stats.groupby(["Player", "Year"]).apply(extract_total_row)
	while isinstance(player_stats.index[0], tuple):
		player_stats.index = player_stats.index.droplevel()

	team_name_mapping = {
		"ATL": "Atlanta Hawks",
		"BOS": "Boston Celtics",
		"BRK": "Brooklyn Nets",
		"CHO": "Charlotte Hornets",
		"CHI": "Chicago Bulls",
		"CLE": "Cleveland Cavaliers",
		"DAL": "Dallas Mavericks",
		"DEN": "Denver Nuggets",
		"DET": "Detroit Pistons",
		"GSW": "Golden State Warriors",
		"HOU": "Houston Rockets",
		"IND": "Indiana Pacers",
		"LAL": "Los Angeles Lakers",
		"LAC": "Los Angeles Clippers",
		"MEM": "Memphis Grizzlies",
		"MIA": "Miami Heat",
		"MIL": "Milwaukee Bucks",
		"MIN": "Minnesota Timberwolves",
		"NOP": "New Orleans Pelicans",
		"NYK": "New York Knicks",
		"OKC": "Oklahoma City Thunder",
		"ORL": "Orlando Magic",
		"PHI": "Philadelphia 76ers",
		"PHO": "Phoenix Suns",
		"POR": "Portland Trail Blazers",
		"SAC": "Sacramento Kings",
		"SAS": "San Antonio Spurs",
		"TOR": "Toronto Raptors",
		"UTA": "Utah Jazz",
		"WAS": "Washington Wizards"
	}

	player_stats["Team"] = player_stats["Team"].map(team_name_mapping)

	return mvp_stats, player_stats, team_stats

def create_stats_basetable(mvp_stats, player_stats, team_stats):
	"""
	Merge datasets into dataset of MVP, player, and team statistics.
	"""
	stats = mvp_stats.merge(
		player_stats, how="outer", on=["Player", "Year"]
	).merge(
		team_stats, how="outer", on=["Team", "Year"]
	)
	for col in ["Pts Won", "Pts Max", "Share"]:
		stats[col].fillna(0, inplace=True)
	stats.apply(pd.to_numeric, errors="ignore")
	stats["GB"] = stats["GB"].str.replace("—", "0")
	stats["GB"] = stats["GB"].apply(pd.to_numeric)
	stats = stats.fillna(0)
	for col in stats.columns:
		stats[col] = pd.to_numeric(stats[col], errors="ignore")
	
	return stats

def merge_boxscores(schedule_dict, boxscore_dict):
	schedule = schedule_dict["schedule"]
	schedule = schedule[schedule.Date != "Playoffs"]
	schedule.rename(columns={
		"Start (ET)": "Start_time",
		"PTS": "Visitor_pts",
		"PTS.1": "Home_pts",
		"Attend.": "Attendance"
	}, inplace=True)
	input_format = "%a, %b %d, %Y"
	schedule["Date"] = schedule["Date"].apply(lambda date: datetime.strptime(date, input_format))
	schedule = schedule[["Date", "Start_time", "Visitor_pts", "Home_pts", "Attendance"]]
	four_factors = boxscore_dict["four_factors"]
	line_score = boxscore_dict["line_score"]
	team_stats = boxscore_dict["team_stats"]
	four_factors = boxscore_dict["four_factors"]
	four_factors.rename(columns={"Unnamed: 0_level_1": "Team"}, inplace=True)
	line_score = boxscore_dict["line_score"]
	line_score.rename(columns={
		"Unnamed: 0_level_1": "Team",
		"1": "Q1",
		"2": "Q2",
		"3": "Q3",
		"4": "Q4",
		"T": "Total"
	}, inplace=True)
	line_score.drop(columns="Team", inplace=True)
	boxscore_stats = schedule.merge(
		four_factors, how="outer", on="Date"
	).merge(
		line_score, how="outer", on="Date"
	).merge(
		team_stats, how="outer", on="Date"
	)

	return boxscore_stats
