import pandas as pd

nfl = pd.read_csv("/Users/adambeaudet/Github/collegeGuesser/data/nfl_players.csv")
nhl = pd.read_csv("/Users/adambeaudet/Github/collegeGuesser/data/nhl_players.csv")
nba = pd.read_csv("/Users/adambeaudet/Github/collegeGuesser/data/nba_players.csv")
mlb = pd.read_csv("/Users/adambeaudet/Github/collegeGuesser/data/mlb_players.csv")

players_db = pd.concat([nfl, nhl, nba, mlb], ignore_index=True)

players_db = players_db[~players_db['full_name'].isin(['Player Invalid', 'Duplicate Player'])]
players_db = players_db[players_db['college'].notna()].copy()

correct_guesses = 0
total_guesses = 0

while True:
    random_player = players_db.sample(n=1)

    print('Where did', random_player['full_name'].values[0], 'go to college?')

    my_guess = input("")

    total_guesses += 1
    if my_guess.lower() == random_player['college'].values[0].lower():
        print("Correct!")
        correct_guesses += 1

    else:
        print("Incorrect.", random_player['full_name'].values[0], 'went to', random_player['college'].values[0])

    print(f"Score: {correct_guesses}/{total_guesses}")
