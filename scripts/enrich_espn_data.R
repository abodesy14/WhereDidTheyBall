# this script is used to fill in any gaps between source systems
# the sleeper api is missing a lot of espn ids that we can backfill via the espn api
# use until we find endpoint for colleges through espn
# since espn id is missing and player_id is specific to sleeper, we'll attempt to join on name
# names can be duplicated so we will dedupe before attempting
# we want to impute espn id so we can possibly enrich this data with statistics, headshots, etc.
# should use espn as base, and join in who we can from sleeper where college is filled in

library(dplyr)
library(glue)
library(here)
library(stringr)

sport = 'nfl'

sleeper_path = here("data", "sleeper", glue("{sport}_players.csv"))
espn_path = here("data", "espn", glue("{sport}_espn_api_players.csv"))
output_dir = here("data", "combined_sources")

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# espn api data - base
# convert experience and display weight to numeric
# see how many name neighbors we have
espn_players <- read.csv(espn_path) %>%
    mutate(experience = as.numeric(str_extract(experience, "\\d+"))) %>%
    mutate(displayWeight = as.numeric(str_extract(displayWeight, "\\d+"))) %>%
    select(id, firstName, lastName, fullName, jersey, displayWeight, displayHeight, age, dateOfBirth, experience, active) %>%
    rename(espn_id = id) %>%
    group_by(fullName) %>%
    mutate(name_count = n()) %>%
    ungroup()

# sleeper api data
# mark duplicates and only join non-duplicates by name
# some duplicates may flow through, we will choose better record aka one with more filled in value
sleeper_players <- read.csv(sleeper_path) %>%
    select(espn_id, full_name, college, high_school, sportradar_id, fantasy_data_id, 
           rotoworld_id, yahoo_id, years_exp, age, status, birth_date, team_abbr, 
           height, weight, sport, position) %>%
    mutate(non_na_count = rowSums(!is.na(.))) %>%
    group_by(espn_id, full_name) %>%
    arrange(desc(non_na_count)) %>%
    slice(1) %>%
    ungroup() %>%
    select(-non_na_count) %>%
    group_by(full_name) %>%
    mutate(is_duplicate_name = n() > 1) %>%
    ungroup()


# join by espn_id where available
joined <- left_join(espn_players, sleeper_players, by = "espn_id", suffix = c("_espn", "_sleeper")) %>%
    mutate(college_join_method = if_else(!is.na(college), "espn_id", NA_character_))

# for rows still missing college, try joining by name, non-dupes only
# filter out names that are duplicated in ESPN data
# also exclude names that are duplicated in ESPN
sleeper_non_dupes <- sleeper_players %>%
    filter(is_duplicate_name == FALSE) %>%
    anti_join(
        espn_players %>% filter(name_count > 1) %>% select(fullName),
        by = c("full_name" = "fullName")
    ) %>%
    select(full_name, college, high_school, position, team_abbr)

# only join by name for rows where college is still null
rows_needing_name_match <- joined %>%
    filter(is.na(college))

rows_with_college <- joined %>%
    filter(!is.na(college))

# do the name match only on rows that need it
rows_needing_name_match <- rows_needing_name_match %>%
    left_join(sleeper_non_dupes, by = c("fullName" = "full_name"), suffix = c("", "_name_match")) %>%
    mutate(
        college = coalesce(college, college_name_match),
        high_school = coalesce(high_school, high_school_name_match),
        position = coalesce(position, position_name_match),
        team_abbr = coalesce(team_abbr, team_abbr_name_match),
        college_join_method = if_else(!is.na(college_name_match), "name_match", NA_character_)
    ) %>%
    select(-ends_with("_name_match"))

# combine back together
joined <- bind_rows(rows_with_college, rows_needing_name_match)

# coalesce overlapping fields
final <- joined %>%
    mutate(
        height = coalesce(displayHeight, height),
        weight = coalesce(displayWeight, weight),
        age = coalesce(age_espn, age_sleeper),
        dob = coalesce(dateOfBirth, birth_date),
        experience = coalesce(experience, years_exp),
        status = coalesce(active, status)
    ) %>%
    select(espn_id, firstName, lastName, fullName, jersey, college, college_join_method,
           high_school, position, team_abbr, height, weight, age, dob, experience, status, name_count)

write.csv(final, file.path(output_dir, glue("{sport}_players_imputed.csv")), row.names = FALSE)