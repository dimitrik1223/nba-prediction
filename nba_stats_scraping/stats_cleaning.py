import pandas as pd

def extract_total_row(df):
	if df.shape[0] == 1:
		return df
	else:
		team = df.iloc[-1, :]["Team"]
		df = df[df["Team"] == "TOT"]
		df["Team"] = team
		return df

def clean_data(mvp_df, players_df, team_standings_df):
	mvp = mvp_df[["Player", "Year", "Pts Won", "Pts Max", "Share"]]
	del players_df['Rk']

	# Remove asteriks from hall of famers 
	players_df["Player"] = players_df["Player"].str.replace("*", "", regex=False)
	players_df.rename(columns={"Tm": "Team"}, inplace=True)
	team_standings_df["Team"] = team_standings_df["Team"].str.replace("*", "", regex=False)
	players_df = players_df.groupby(["Player", "Year"]).apply(extract_total_row)
	for i in range(len(players_df.index[0]) - 1):
		players_df.index = players_df.index.droplevel()

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

	players_df["Team"] = players_df["Team"].map(team_name_mapping)

	return mvp_df, players_df, team_standings_df

def create_stats_basetable(mvp_df, players_df, team_standings_df):
	all_stats_df = mvp_df.merge(
		players_df, how="outer", on=["Player", "Year"]
	).merge(
		team_standings_df, how="outer", on=["Team", "Year"]
	)
	for col in ["Pts Won", "Pts Max", "Share"]:
		all_stats_df[col].fillna(0, inplace=True)
	all_stats_df.apply(pd.to_numeric, errors="ignore")
	all_stats_df["GB"] = all_stats_df["GB"].str.replace("—", "0")
	all_stats_df["GB"] = all_stats_df["GB"].apply(pd.to_numeric)
	stats = all_stats_df.fillna(0)
	for col in stats.columns:
		stats[col] = pd.to_numeric(stats[col], errors="ignore")

	return stats

	
	
