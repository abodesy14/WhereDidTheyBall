import requests
import pandas as pd

player_spine = pd.read_csv("/Users/adambeaudet/Github/collegeGuesser/data/espn/nfl_espn_api_players.csv")
player_spine = player_spine[['id', 'fullName', 'firstName', 'lastName']]


for index, row in player_spine.iterrows():
    first_name = row['firstName']
    last_name = row['lastName']
    full_name = row['fullName']
    player_id = row['id']

    # skip if missing - won't be able to construct url
    if pd.isna(first_name) or pd.isna(last_name):
        continue

    first_id = first_name[:2]
    last_id = last_name[:4]
    id = last_id + first_id + '00'
    letter = last_name[0]

    root_url = f'https://www.pro-football-reference.com/players/{letter}/{id}.htm'
    print(root_url)