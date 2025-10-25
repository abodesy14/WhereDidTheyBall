import requests
import csv
from time import sleep, time
from datetime import datetime
import pandas as pd
from pathlib import Path

# scrape one league at a time
sport = 'football'

sport_map = {
    'football': 'nfl',
    'baseball': 'mlb',
    'hockey': 'nhl',
    'basketball': 'nba'
}

league = sport_map.get(sport, 'unknown')

headers = {"User-Agent": "college-script/1.0"}

# v3 endpoint gets height, weight, dob, experience, etc.
# v2 endpoint gets college information
v3_list_url = f"https://sports.core.api.espn.com/v3/sports/{sport}/{league}/athletes?limit=18000"
v2_ath_url = f"https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/athletes/{{}}"

script_directory = Path(__file__).resolve().parent
data_directory = script_directory.parent / "data" / "espn"
output_csv = data_directory / f"{league}_espn_api_players.csv"

# cache to avoid redundant calls
college_cache = {}
team_cache = {}

def get_json(url):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        return None

def get_college_info(col_ref):
    if not col_ref:
        return (None, None)
    if col_ref in college_cache:
        return college_cache[col_ref]
    col_data = get_json(col_ref)
    if col_data:
        name = col_data.get("name")
        college_id = col_data.get("id")
        college_cache[col_ref] = (name, college_id)
        return (name, college_id)
    college_cache[col_ref] = (None, None)
    return (None, None)

def get_colleges(v2_data):
    # try collegeAthlete first as that looks to be more reliable
    ca_ref = (v2_data.get("collegeAthlete") or {}).get("$ref")
    if ca_ref:
        ca_data = get_json(ca_ref)
        if ca_data:
            col_ref = (ca_data.get("college") or {}).get("$ref")
            if col_ref:
                name, college_id = get_college_info(col_ref)
                if name:
                    return (name, college_id, "collegeAthlete")
    
    # fallback to direct college field if collegeAthlete doesn't work
    col_ref = (v2_data.get("college") or {}).get("$ref")
    if col_ref:
        name, college_id = get_college_info(col_ref)
        if name:
            return (name, college_id, "direct")
    return ("", None, None)

def get_team_abbrev(team_ref):
    if not team_ref:
        return ""
    if team_ref in team_cache:
        return team_cache[team_ref]
    team_data = get_json(team_ref)
    if team_data:
        abbrev = team_data.get("abbreviation") or team_data.get("abbrev")
        team_cache[team_ref] = abbrev
        return abbrev
    team_cache[team_ref] = ""
    return ""

def get_position(v2_data):
    if not v2_data:
        return ""
    pos_ref = (v2_data.get("position") or {}).get("$ref")
    if pos_ref:
        pos_data = get_json(pos_ref)
        if pos_data:
            return pos_data.get("abbreviation") or pos_data.get("name", "")
    return ""

# get current timestamp each time we run this
processed_ts = datetime.now().isoformat()

# return all players with pagination
all_athletes = []
page = 1

while True:
    url = f"{v3_list_url}&page={page}"
    v3_json = get_json(url)
    
    if not v3_json:
        print(f"Failed to fetch page {page}")
        break
    
    items = v3_json.get("items", [])
    if not items:
        break
    
    all_athletes.extend(items)
    print(f"  Got {len(items)} athletes from page {page} (Total: {len(all_athletes)})")
    
    # check if there are more pages to scrape
    page_count = v3_json.get("pageCount", 1)
    if page >= page_count:
        break
    
    page += 1
    sleep(0.5)

print(f"\nTotal athletes fetched: {len(all_athletes)}")

# exclude specific IDs. bad/irrelevant data
exclude_ids = {"4246273", "4246281", "4246289", "4246247", "4246272", "4246274"}
athletes = [a for a in all_athletes if str(a.get("id")) not in exclude_ids]


results = []
start_time = time()

for i, athlete in enumerate(athletes):
    aid = athlete.get("id")
    v2_data = get_json(v2_ath_url.format(aid))
    
    draft = v2_data.get("draft", {}) if v2_data else {}
    draft_team_ref = (draft.get("team") or {}).get("$ref")
    team_ref = (v2_data.get("team") or {}).get("$ref") if v2_data else None
    birthPlace = athlete.get("birthPlace") or {}
    
    # get college with source and ID
    college, college_id, college_source = get_colleges(v2_data) if v2_data else ("", None, None)
    
    row = {
        "id": aid,
        "league": league,
        "fullName": athlete.get("fullName"),
        "firstName": athlete.get("firstName"),
        "lastName": athlete.get("lastName"),
        "position": get_position(v2_data),
        "jersey": athlete.get("jersey"),
        "active": athlete.get("active"),
        "weight": athlete.get("weight"),
        "height": athlete.get("height"),
        "age": athlete.get("age"),
        "dateOfBirth": athlete.get("dateOfBirth"),
        "experience_years": (athlete.get("experience") or {}).get("years"),
        "birthCity": birthPlace.get("city", ""),
        "birthState": birthPlace.get("state", ""),
        "birthCountry": birthPlace.get("country", ""),
        "debutYear": v2_data.get("debutYear") if v2_data else "",
        "college": college,
        "collegeId": college_id,
        "college_source": college_source,
        "draftYear": draft.get("year", ""),
        "draftRound": draft.get("round", ""),
        "draftPick": draft.get("selection", ""),
        "draftTeam": get_team_abbrev(draft_team_ref),
        "team": get_team_abbrev(team_ref),
        "processed_ts": processed_ts
    }
    
    results.append(row)
    
    # progress tracker
    if (i + 1) % 10 == 0:
        elapsed = time() - start_time
        rate = (i + 1) / elapsed
        remaining = (len(athletes) - (i + 1)) / rate
        print(f"Processed {i + 1}/{len(athletes)} - {rate:.1f}/sec - Est. {remaining/60:.1f} min remaining")
    
    # sleep between api requests
    sleep(0.05)

# load existing data if file exists
if output_csv.exists():
    existing_df = pd.read_csv(output_csv)
    print(f"Loaded {len(existing_df)} existing records")
else:
    existing_df = pd.DataFrame()
    print("No existing file found, creating new dataset")

new_df = pd.DataFrame(results)

# combine old and new data
if not existing_df.empty:
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
else:
    combined_df = new_df

if 'is_latest' in combined_df.columns:
    combined_df = combined_df.drop(columns=['is_latest'])

# ensure id is string
combined_df['id'] = combined_df['id'].astype(str)

# sort most recent first
combined_df = combined_df.sort_values('processed_ts', ascending=False)

# SCD table - mark is_latest 1 for most recent record per id, 0 for all others
combined_df['is_latest'] = 0
mask = ~combined_df.duplicated(subset=['id'], keep='first')
combined_df.loc[mask, 'is_latest'] = 1
combined_df.to_csv(output_csv, index=False)

elapsed = time() - start_time
print(f"\nDone! Processed {len(new_df)} players in {elapsed/60:.1f} minutes")
print(f"Total records: {len(combined_df)}")
print(f"Latest records: {len(combined_df[combined_df['is_latest'] == 1])}")
print(f"Historical records: {len(combined_df[combined_df['is_latest'] == 0])}")

# show college source breakdown for latest records
latest = combined_df[combined_df['is_latest'] == 1]
print(f"\nCollege source breakdown (latest records):")
print(f"From collegeAthlete: {len(latest[latest['college_source'] == 'collegeAthlete'])}")
print(f"From direct: {len(latest[latest['college_source'] == 'direct'])}")
print(f"No college found: {len(latest[latest['college_source'].isna()])}")