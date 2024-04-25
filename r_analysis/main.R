source("ini.R")

SimulationData <- import('../simulation/output/simulation_all_2022.csv')


# source("rdata_load.R")

CountData <- SimulationData %>%
  group_by(date) %>%
  summarise(car_demand_count = n_distinct(car_id),
            station_used_count = n_distinct(station_id),
            mean_charging_time = median(elapsed_time[event_name == 'charge - finish'], na.rm=TRUE)/60/60,
            mean_waiting_time_til_available = median(elapsed_time[event_name == 'queue - charge'], na.rm=TRUE)/60/60,
            mean_waiting_time_til_give_up = median(elapsed_time[event_name == 'queue - give up'], na.rm=TRUE)/60/60,
            queue_count = sum(event_name=='arrive - queue', na.rm=TRUE),
            give_up_count = sum(event_name=='queue - give up', na.rm=TRUE),
            percentage_queue = queue_count/car_demand_count,
            percentage_give_up = give_up_count/car_demand_count) %>%
  ungroup()

