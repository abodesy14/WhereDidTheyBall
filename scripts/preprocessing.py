import pandas as pd
from pathlib import Path
import requests

script_directory = Path(__file__).resolve().parent
data_directory = script_directory.parent / "data"
espn_directory = data_directory / "espn" / "player_profiles"
app_directory = data_directory / "app_data"
accepted_answers_directory = data_directory / "manual"

player_stats = pd.read_csv("../data/espn/statistics/espn_api_player_statistics.csv")

leagues = ['nfl', 'nhl', 'nba', 'mlb']
dfs = []

for league in leagues:
    file_path = espn_directory / f"{league}_espn_api_player_profiles.csv"
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
# player_college_data = player_college_data.merge(player_stats, left_on="id", right_on="athlete_id", how="left")
# need to join on athlete id and sport ^

output_path = app_directory / "player_profile_data.csv"
player_college_data.to_csv(output_path, index=False)