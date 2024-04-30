# LOAD R DATA

files_source <- file.path("DATA",
                          list.files("DATA"))

r_files <- files_source %>%
  map_chr(~ str_extract(., "^.+\\.Rdata"))

r_files <- r_files[!is.na(r_files)]

for (i in 1:length(r_files))
{
  load(r_files[i])
}
