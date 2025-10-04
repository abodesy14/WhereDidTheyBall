# this script is used to fill in any gaps between source systems
# the sleeper api is missing a lot of espn ids that we can backfill via the espn api
# maybe there's an espn endpoint that would return college, but for now we'll use sleeper
# since espn id is missing and player_id is specific to sleeper, we'll attempt to join on name
# names can be duplicated so we will dedupe before attempting
# we want to impute espn id so we can possibly enrich this data with statistics, headshots, etc.
# should use espn as base, and join in who we can from sleeper where college filled in

library(dplyr)
library(glue)
library(here)

sport = 'nfl'

sleeper_path = here("data", "sleeper", glue("{sport}_players.csv"))
espn_path = here("data", "espn", glue("{sport}_espn_api_players.csv"))
output_dir = here("data", "combined_sources")

# sleeper export
sleeper_players <- read.csv(sleeper_path) %>%
    group_by(full_name) %>%
    mutate(dupes = n()) %>%
    mutate(has_duplicate_name = ifelse(dupes > 1, 1, 0)) %>%
    filter(has_duplicate_name == 0) %>%
    select(-c(has_duplicate_name))

# espn api export
espn_players = read.csv(espn_path) %>%
    group_by(fullName) %>%
    mutate(dupes = n()) %>%
    mutate(has_duplicate_name = ifelse(dupes > 1, 1, 0)) %>%
    filter(has_duplicate_name == 0) %>%
    select(id, fullName)

# whole point of this join is to impute espn_id if it's null in nfl_players df
join_sources <- left_join(sleeper_players, espn_players, by = c("full_name" = "fullName")) %>%
    select(names(sleeper_players), id)

# coalesce espn api "id" and espn_id from sleeper api
join_sources <- join_sources %>%
    mutate(espn_id = coalesce(espn_id, id)) %>%
    select(-c(id))

# filtered df of duplicated names that we'll union back together with non-dupe df
sleeper_players_name_dupes <- read.csv(sleeper_path) %>%
    group_by(full_name) %>%
    mutate(dupes = n()) %>%
    mutate(has_duplicate_name = ifelse(dupes > 1, 1, 0)) %>%
    filter(has_duplicate_name == 1) %>%
    select(-c(has_duplicate_name))

# bind together data so original grain is restored
all_players <- rbind(join_sources, sleeper_players_name_dupes)

write.csv(all_players, file.path(output_dir, glue("{sport}_players_imputed.csv")), row.names = FALSE)
