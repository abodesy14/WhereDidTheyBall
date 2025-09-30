import requests
import pandas as pd

sport = 'nfl'
root_url = f'https://api.sleeper.app/v1/players/{sport}'

response = requests.get(root_url)
response.raise_for_status()
data = response.json()

df = pd.DataFrame.from_dict(data, orient="index").reset_index().rename(columns={"index": "player_id"})

df.to_csv(f"{sport}_players.csv", index=False)
