import pandas as pd
import numpy as np
import h3
import simpy
from datetime import datetime, timedelta
# import folium     # for jupyter notebooks only
import library.mong_connection as mongo
import library.config as cfg
import data_processing as dpr
import car_simulation as sim
import os

refresh = False
rerun_simulation = True
simulation_level = 7
env = simpy.Environment()
now = datetime.combine(datetime.now().date() + timedelta(days=1), 
                       datetime.min.time())

# Analyse data
if refresh:
    traffic_allocation = dpr.extract_traffic_data()
    station_data_simulation = dpr.extract_station_data(simulation_level)
    ports_data = dpr.extract_charging_port_data()
    raw_station_data, raw_hex_data = dpr.process_traffic_data()

    traffic_allocation.to_csv('simulation/sys_files/generated_file/traffic_allocation.csv')
    station_data_simulation.to_csv('simulation/sys_files/generated_file/station_data_simulation.csv')
    ports_data.to_csv('simulation/sys_files/generated_file/ports_data.csv')
    raw_station_data.to_csv('simulation/sys_files/generated_file/raw_station_data.csv')
    raw_hex_data.to_csv('simulation/sys_files/generated_file/raw_hex_data.csv')

# Run simulation
if rerun_simulation:
    # Generate Simulation data
    sim_car_list = sim.generate_car_list()
    sim_station_list = sim.generate_staion(env)
    log_df = pd.DataFrame(columns=['timestamp', 'car_id', 'station_id', 'event_name'])

    for id, ev in sim_car_list.iterrows():
        # chosen_station = dict(car_list[car_list['CarId'] == id].head(1))['ChargeDeviceId'].values[0]
        chosen_station = ev['ChargeDeviceId']
        # car_info = dict(car_list[car_list['CarId'] == id].head(1))
        station_info = dict(sim_station_list[sim_station_list['ChargeDeviceId'] == chosen_station].head(1))
        # station_name = station_info['ChargeDeviceName'].values[0]
        charge_time = ev['ChargeTime']
        resource = station_info['Station'].values[0]
        env.process(sim.car(env,id,chosen_station,resource,charge_time,now,log_df))
    env.run()
    log_df.to_csv('simulation/output/log/'+datetime.now().strftime("%Y%m%d%H%M")+'_sim_result.log')
    log_df.to_csv('simulation/sys_files/latest_sim_result.csv')






print(log_df)

