import requests
import pandas as pd

sport = 'nba'
root_url = f'https://api.sleeper.app/v1/players/{sport}'

response = requests.get(root_url)
response.raise_for_status()
data = response.json()

df = pd.DataFrame.from_dict(data, orient="index").reset_index(drop=True)

# extract college from metadata if it exists and top-level college is empty
def get_college(row):
    # first try top-level college
    if pd.notna(row.get('college')) and row.get('college') != '':
        return row['college']
    # then try metadata
    if pd.notna(row.get('metadata')) and isinstance(row['metadata'], dict):
        metadata_college = row['metadata'].get('college', '')
        if metadata_college and metadata_college != '':
            return metadata_college
    return None

df['college'] = df.apply(get_college, axis=1)

df.to_csv(f"{sport}_players.csv", index=False)