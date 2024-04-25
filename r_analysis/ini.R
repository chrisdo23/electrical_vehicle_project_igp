# CLEAN EVIRONMENT ===============

#rm(list = ls(all.names = TRUE)) #will clear all objects includes hidden objects.
#gc() #free up memrory and report the memory usage.

# INITIALIZATION =================

pacman::p_load(pacman,
               DT,
               tidyverse,
               tidyselect,
               rmarkdown,
               tibble,
               dplyr,
               purrr,
               knitr,
               kableExtra,
               zoo,
               lubridate,
               plotly,
               rio,
               stringr,
               tidyr,
               janitor,
               highcharter,
               tibble,
               bigrquery,
               googlesheets4,
               googledrive,
               readxl,
               openxlsx,
               DBI,
               gargle,
               telegram.bot,
               bigrquery,
               ggplot2,
               scales,
               viridis,
               ggpubr)

# IMPORT FUNCTIONS ============

files_source <- file.path("FUNCTIONS",
                          list.files("FUNCTIONS"))

r_files <- files_source %>%
  map_chr(~ str_extract(., "^.+\\.R"))

r_files <- r_files[!is.na(r_files)]

walk(r_files, source)

rm(files_source)
rm(r_files)


# IMPORT QUERY

files_source <- file.path("QUERY",
                          list.files("QUERY"))

r_files <- files_source %>%
  map_chr(~ str_extract(., "^.+\\.R"))

r_files <- r_files[!is.na(r_files)]

walk(r_files, source)

rm(files_source)
rm(r_files)
