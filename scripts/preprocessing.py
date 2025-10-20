import pandas as pd
from pathlib import Path
import requests

script_directory = Path(__file__).resolve().parent
data_directory = script_directory.parent / "data"
espn_directory = data_directory / "espn"
app_directory = data_directory / "app_data"
accepted_answers_directory = data_directory / "manual"

leagues = ['nfl', 'nhl', 'nba', 'mlb']
dfs = []

for league in leagues:
    file_path = espn_directory / f"{league}_espn_api_players.csv"
    df = pd.read_csv(file_path)
    dfs.append(df)

player_college_data = pd.concat(dfs)

# filter out players with no college
# filter to just most recent pull of each player
# filter out players with no position
# filter out players with no experience
player_college_data = player_college_data[player_college_data['college'].notna()]
player_college_data = player_college_data[player_college_data['is_latest'] == 1]
player_college_data = player_college_data[player_college_data['position'] != '-']
player_college_data = player_college_data[player_college_data['experience_years'].notna()]

output_path = app_directory / "player_college_data.csv"
player_college_data.to_csv(output_path, index=False)