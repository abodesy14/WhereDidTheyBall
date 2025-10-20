import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

player_spine = pd.read_csv("/data/app_data/player_college_data.csv")
player_spine = player_spine[['id', 'fullName', 'firstName', 'lastName']]

results = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for index, row in player_spine.iterrows():
    first_name = row['firstName']
    last_name = row['lastName']
    full_name = row['fullName']
    player_id = row['id']

    if pd.isna(first_name) or pd.isna(last_name):
        continue

    first_id = first_name[:2]
    last_id = last_name[:4]
    id = last_id + first_id + '00'
    letter = last_name[0]

    root_url = f'https://www.pro-football-reference.com/players/{letter}/{id}.htm'

    try:
        response = requests.get(root_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        college = None
        meta_div = soup.find('div', {'id': 'meta'})
        if meta_div:
            # look for link with /schools/ in href, not /cfb/
            college_link = meta_div.find('a', href=lambda x: x and '/schools/' in x and '/schools/high_schools' not in x)
            if college_link:
                college = college_link.text.strip()
        
        results.append({'id': player_id, 'fullName': full_name, 'college': college})
        print(f"{full_name}: {college if college else 'Not found'}")
        
    except Exception as e:
        print(f"Failed: {full_name} - {e}")
        results.append({'id': player_id, 'fullName': full_name, 'college': None})
    
    time.sleep(5)

results_df = pd.DataFrame(results)
results_df.to_csv('pfr_colleges.csv', index=False)