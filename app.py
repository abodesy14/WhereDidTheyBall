import streamlit as st
import pandas as pd
import requests
from pathlib import Path

data_directory = Path(__file__).resolve().parent / "data" / "app_data"
player_data = data_directory / "player_college_data.csv"
accepted_answers = pd.read_csv("data/manual/accepted_answers.csv")

# accepted answer aliases
# choosing to allow free form text answers rather than dropdown for now
accepted_answers["aliases"] = accepted_answers.apply(
    lambda row: [str(v).strip().lower() for v in [
            row.get("college"),
            row.get("display_name"),
            row.get("variant_1"),
            row.get("variant_2"),
            row.get("variant_3"),
            row.get("variant_4"),
            row.get("variant_5"),
            row.get("variant_6")
        ]
        if pd.notna(v)
    ],
    axis=1
)

# lookup dictionary
alias_lookup = {
    row["collegeId"]: row["aliases"]
    for _, row in accepted_answers.iterrows()
}

@st.cache_data


def load_all_players():
    df = pd.read_csv(player_data)
    df["id"] = df["id"].astype(str)
    return df


def init_session(players):
    if "players_pool" not in st.session_state:
        st.session_state.players_pool = players.copy()
    if "current" not in st.session_state:
        st.session_state.current = None
    if "correct" not in st.session_state:
        st.session_state.correct = 0
    if "total" not in st.session_state:
        st.session_state.total = 0
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "answered_current" not in st.session_state:
        st.session_state.answered_current = False
    if "challenged_last" not in st.session_state:
        st.session_state.challenged_last = False

def challenge_last_answer():
    '''
    Function for answers given by user that they believe to be correct and/or typos. 
    1 gets added to the users score when the "challenge flag" button is clicked.
    '''

    st.session_state.correct += 1
    st.session_state.challenges += 1
    st.session_state.challenged_last = True


def pick_player(filtered):
    '''
    Picks a player at random to be presented to the user.
    Returns None if no players match the filtered criteria.
    '''

    if filtered.empty:
        return None 
    sample_df = filtered.sample(n=1)
    return sample_df.iloc[0]



st.set_page_config(page_title="Where Did They Ball?", layout="centered")

# reduce whitespace at top of app
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Where Did They Ball?")
st.caption("Test your ball knowledge by guessing where athletes played in college")

players = load_all_players()


# sidebar filters and controls
with st.sidebar:
    st.header("Setup")

    sports = {"All": "all", "NFL": "nfl", "NBA": "nba", "MLB": "mlb", "NHL": "nhl"}

    sport_label = st.radio(
        "Sport",
        options=list(sports.keys()),
        index=0,
        horizontal=True,
    )

    # map back to lowercase for filtering
    sport_choice = sports[sport_label]

    # want position to be second filter in sidebar panel but it depends on status_choice
    # put a placeholder here so we can fill it after
    pos_placeholder = st.empty()

    # compute position options after knowing status_choice filter
    filtered_players = players.copy()

    # print number of players in active status group in parenthesis after position
    if sport_choice == "all":
        pos_counts = filtered_players["position"].dropna().value_counts()
    else:
        pos_counts = (
            filtered_players.loc[filtered_players["league"] == sport_choice, "position"]
            .dropna()
            .value_counts()
        )

    pos_labels = [f"{pos} ({count:,})" for pos, count in pos_counts.items()]
    pos_choice = pos_placeholder.selectbox(
        "Position", options=["All"] + pos_labels, index=0)

    # prefer All to be printed rather than blank
    if pos_choice == "All":
        pos_choice_clean = ""
    else:
        pos_choice_clean = pos_choice.split(" (")[0]


    # team filter - should depend on sport and status
    team_placeholder = st.empty()

    if sport_choice == "all":
        teams = filtered_players["team"].dropna().unique()
    else:
        teams = (
            filtered_players.loc[filtered_players["league"] == sport_choice, "team"]
            .dropna()
            .unique()
        )

    teams = sorted(teams)

    # persist across other filtrations if valid
    if "team_choice" not in st.session_state:
        st.session_state.team_choice = "All"

    # reset to all if selection isn't valid anymore 
    # ex: you're filtered to CHW which is an MLB team, and then select NFL as a filter
    if st.session_state.team_choice not in (["All"] + list(teams)):
        st.session_state.team_choice = "All"

    team_choice = team_placeholder.selectbox(
        "Team",
        options=["All"] + list(teams),
        index=(["All"] + list(teams)).index(st.session_state.team_choice),
        key="team_choice",
    )


    status_choice = st.radio("Player Status", options=["Active", "All Players"], index=0)

    st.markdown(
    "> ⚠️ **Note:** Data comes from ESPN and may not include full transfer history. Usually only the most recent college is available.")


    if st.button("Reset session / start over"):
        # reset session state with full player pool
        st.session_state.players_pool = players.copy()
        st.session_state.current = None
        st.session_state.correct = 0
        st.session_state.total = 0
        st.session_state.last_result = None
        st.session_state.answered_current = False


# if filter gets applied mid question, switch to that sport before answering, not after
# gives the illusion that filter doesn't work if not
filter_state = {
    "sport": sport_choice,
    "position": pos_choice_clean,
    "active": status_choice,
    "team": st.session_state.get("team_choice", "All"),
}

if "last_filters" not in st.session_state:
    st.session_state.last_filters = filter_state
else:
    if st.session_state.last_filters != filter_state:
        # force new player selection if filter changes
        st.session_state.current = None
        st.session_state.answered_current = True
        st.session_state.last_filters = filter_state


# initialize session state
init_session(players)

# compute available pool according to sidebar filters
pool = st.session_state.players_pool

# filter by sport
if sport_choice != "all":
    pool = pool[pool["league"] == sport_choice]

# filter by position
if pos_choice_clean:
    pool = pool[pool["position"].fillna("").str.upper() == pos_choice_clean.strip().upper()]

# apply team filter from session state
team_choice = st.session_state.get("team_choice", "All")
if team_choice != "All":
    pool = pool[pool["team"].fillna("") == team_choice]

# filter by active status
if status_choice == "Active":
    pool = pool[pool["active"] == True]

# show remaining count
st.write(f"Players matching current filters: **{len(pool):,}**")


# pick a player when there's none selected and we've moved past the previous answer
if st.session_state.current is None or st.session_state.answered_current:
    if pool.empty:
        st.warning("No players match your filters.")
        st.session_state.current = None
    else:
        st.session_state.current = pick_player(pool)
        st.session_state.answered_current = False
        st.session_state.challenged_last = False

# main card
# show current player stats
if st.session_state.current is not None:
    current = st.session_state.current
    name = current["fullName"]
    pos = current.get("position", "")
    team = current.get("team", "")
    league = current.get("league", "")
    experience = current.get("experience_years", "")
    experience = int(experience) if pd.notna(experience) else 0
    draft_year = current.get("draftYear")
    draft_year = int(float(draft_year)) if pd.notna(draft_year) else "Undrafted"    
    draft_round = current.get("draftRound")
    draft_round = int(draft_round) if pd.notna(draft_round) else "Undrafted"
    playing_status = "Active" if str(current.get("active")).upper() == "TRUE" else "Inactive"
        
    # player headshots
    if pd.notna(current.get("id")):
        id = str(int(current["id"]))
        
        # construct endpoints
        headshot_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/{league}/players/full/{id}.png&w=350&h=254"
        fallback_url = f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/{league}.png&w=350&h=254"

        try:
            response = requests.head(headshot_url, timeout=2)
            if response.status_code != 200:
                headshot_url = fallback_url
        except:
            headshot_url = fallback_url
        
        st.image(headshot_url, width=250, use_container_width=False)
    else:
        # maintain layout consistency
        st.markdown('<div style="height: 182px;"></div>', unsafe_allow_html=True)

    st.subheader(name)


    # no need to show draft round if they are undrafted
    if draft_year != "Undrafted":
        st.write(f"Position: {pos} | Team: {team} | Draft Year: {draft_year} | Draft Round: {draft_round} | Experience: {experience} | Status: {playing_status}")
    else:
        st.write(f"Position: {pos} | Team: {team} | Draft Year: {draft_year} | Experience: {experience} | Status: {playing_status}")


    # show last result
    if st.session_state.last_result:
        result_type, correct_college = st.session_state.last_result

        # keep height stable and buttons aligned
        cols = st.columns([3, 1])

        # display answer to user
        with cols[0]:
            if result_type == "correct":
                st.success(f"✓ Previous answer was correct! ({correct_college})")
            else:
                st.error(f"✗ Previous answer was incorrect. Correct answer: {correct_college}")

        with cols[1]:
            # challenge button should always visible so height remains consistent
            # only active for incorrect answers not yet challenged
            challenge_disabled = (
                result_type != "incorrect" or 
                st.session_state.get("challenged_last", False)
            )

            st.button(
                "🚩 Challenge Flag",
                key="challenge_button",
                disabled=challenge_disabled,
                help="Adds 1 to your score if you believe your last answer was correct or a typo.",
                on_click=challenge_last_answer
            )

    if "challenges" not in st.session_state:
        st.session_state.challenges = 0

    # guess form
    with st.form("guess_form", clear_on_submit=True):
        guess = st.text_input(
            "Where did this player go to college?",
            placeholder="Type college name (ie. 'Notre Dame')",
            key="guess_input"
        )

        submitted = st.form_submit_button("Submit guess", use_container_width=True)

        if submitted:
            true_college = str(current["college"]).strip()
            guess_norm = guess.strip().lower()
            college_id = current.get("collegeId")

            st.session_state.total += 1

            # get list of accepted aliases for this college
            accepted = alias_lookup.get(college_id, [])
            correct = guess_norm in accepted

            if correct:
                st.session_state.correct += 1
                st.session_state.last_result = ("correct", accepted_answers.loc[accepted_answers["collegeId"] == college_id, "display_name"].values[0])
            else:
                correct_display = accepted_answers.loc[accepted_answers["collegeId"] == college_id, "display_name"].values[0]
                st.session_state.last_result = ("incorrect", correct_display)

            # drop current player so they won't be asked again during session
            pid = st.session_state.current["id"]
            st.session_state.players_pool = st.session_state.players_pool[
                st.session_state.players_pool["id"] != pid
            ]

            # mark player as answered
            st.session_state.answered_current = True
            
            # re-run to show next player
            st.rerun()

    # score display section
    if st.session_state.total > 0:
        accuracy = (st.session_state.correct / st.session_state.total * 100)
        st.markdown(
            f"**Score:** {st.session_state.correct} / {st.session_state.total}  —  {accuracy:.1f}%"
            + (f"  _({st.session_state.challenges} challenge{'s' if st.session_state.challenges != 1 else ''})_" 
            if st.session_state.challenges > 0 else "")
        )
    else:
        st.markdown(f"**Score:** 0 / 0  —  0.0%")

else:
    st.info("No player selected. Adjust filters or reset the session.")