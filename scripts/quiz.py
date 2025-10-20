import pandas as pd

nfl = pd.read_csv("../data/espn/nfl_espn_api_players.csv")
nhl = pd.read_csv("../data/espn/nhl_espn_api_players.csv")
nba = pd.read_csv("../data/espn/nba_espn_api_players.csv")
mlb = pd.read_csv("../data/espn/mlb_espn_api_players.csv")

players_db = pd.concat([nfl, nhl, nba, mlb], ignore_index=True)

players_db = players_db[~players_db['fullName'].isin(['Player Invalid', 'Duplicate Player'])]
players_db = players_db[players_db['college'].notna()].copy()

correct_guesses = 0
total_guesses = 0

while True:
    random_player = players_db.sample(n=1)
    print('Where did', random_player['fullName'].values[0], 'go to college?')
    my_guess = input("")
    total_guesses += 1
    if my_guess.lower() == random_player['college'].values[0].lower():
        print("Correct!")
        correct_guesses += 1

    else:
        print("Incorrect.", random_player['fullName'].values[0], 'went to', random_player['college'].values[0])

    print(f"Score: {correct_guesses}/{total_guesses}")