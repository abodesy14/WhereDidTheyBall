# eventually convert to python so whole project is in one language

library(tidyverse)

players_df <- read.csv("/data/app_data/player_college_data.csv")

colleges_seed <- players_df %>%
  filter(is_latest == 1) %>%
  group_by(college, collegeId) %>%
  summarise(
    n_players = n_distinct(id),
    leagues = paste(unique(league), collapse = ", ")
  )

accepted_answers <- read.csv("/Users/adambeaudet/Github/collegeGuesser/data/manual/accepted_answers.csv")

missing_mappings <- anti_join(colleges_seed, accepted_answers, by = "collegeId")
join_answers_to_seed <- left_join(colleges_seed, accepted_answers, by = "collegeId")

n_missing <- nrow(missing_mappings)
sys_time <- Sys.time()

output_dir <- "data/inspection"

# write any missing college mappings to separate csv for review
# including timestamp so we know freshness of last check
output_path <- file.path(output_dir, paste0("missing_", n_missing, "_mappings_", sys_time, ".csv"))
write.csv(missing_mappings, output_path, row.names = FALSE)