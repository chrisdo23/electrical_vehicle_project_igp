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
import asyncio
import json

refresh = False
rerun_simulation = False
multi_days_simulation = False

simulation_level = 7
env = simpy.Environment()

# Analyse data
if refresh:
    traffic_allocation = dpr.extract_traffic_data()
    station_data_simulation = dpr.extract_station_data(simulation_level)
    ports_data = dpr.extract_charging_port_data()
    raw_station_data, raw_hex_data = dpr.process_traffic_data()
    business_ref_table = dpr.generate_business_data(raw_hex_data, raw_station_data)

    traffic_allocation.to_csv('simulation/sys_files/generated_file/traffic_allocation.csv')
    station_data_simulation.to_csv('simulation/sys_files/generated_file/station_data_simulation.csv')
    ports_data.to_csv('simulation/sys_files/generated_file/ports_data.csv')
    raw_station_data.to_csv('simulation/sys_files/generated_file/raw_station_data.csv')
    raw_hex_data.to_csv('simulation/sys_files/generated_file/raw_hex_data.csv')
    business_ref_table.to_csv('simulation/sys_files/generated_file/business_ref_table.csv')
else:
    traffic_allocation = pd.read_csv('simulation/sys_files/generated_file/traffic_allocation.csv')
    station_data_simulation = pd.read_csv('simulation/sys_files/generated_file/station_data_simulation.csv')
    ports_data = pd.read_csv('simulation/sys_files/generated_file/ports_data.csv')
    raw_station_data = pd.read_csv('simulation/sys_files/generated_file/raw_station_data.csv')
    raw_hex_data = pd.read_csv('simulation/sys_files/generated_file/raw_hex_data.csv')
    business_ref_table = pd.read_csv('simulation/sys_files/generated_file/business_ref_table.csv')

# Run simulation
if rerun_simulation:
    now = datetime.combine(datetime.now().date() + timedelta(days=1), 
                       datetime.min.time())
    # Generate Simulation data
    sim_car_list = sim.generate_car_list()
    sim_station_list = sim.generate_staion(env)
    log_df = pd.DataFrame(columns=['timestamp', 'car_id', 'station_id', 'event_name', 'elapsed_time'])

    for id, ev in sim_car_list.iterrows():
        # chosen_station = dict(car_list[car_list['CarId'] == id].head(1))['ChargeDeviceId'].values[0]
        chosen_station = ev['ChargeDeviceId']
        # car_info = dict(car_list[car_list['CarId'] == id].head(1))
        station_info = dict(sim_station_list[sim_station_list['ChargeDeviceId'] == chosen_station].head(1))
        # station_name = station_info['ChargeDeviceName'].values[0]
        charge_time = ev['ChargeTime']
        car_id = ev['CarId']
        resource = station_info['Station'].values[0]
        env.process(sim.car(env,car_id,chosen_station,resource,charge_time,now,log_df))
    env.run()
    log_df.to_csv('simulation/output/log/'+datetime.now().strftime("%Y%m%d%H%M")+'_sim_result.log')
    log_df.to_csv('simulation/sys_files/latest_sim_result.csv')

# Run simulation for a continuous x days:
if multi_days_simulation:
    sim_result = pd.DataFrame()
    for i in range(0,7):
        env = simpy.Environment()
        now = datetime.combine(datetime.now().date() + timedelta(days=(1+i)), datetime.min.time())
        # print(1+i)
        # print(str(now))
        # Generate Simulation data
        sim_car_list = sim.generate_car_list()
        sim_station_list = sim.generate_staion(env)
        log_df = pd.DataFrame(columns=['timestamp', 'car_id', 'station_id', 'event_name', 'elapsed_time'])

        for id, ev in sim_car_list.iterrows():
            # chosen_station = dict(car_list[car_list['CarId'] == id].head(1))['ChargeDeviceId'].values[0]
            chosen_station = ev['ChargeDeviceId']
            # car_info = dict(car_list[car_list['CarId'] == id].head(1))
            station_info = dict(sim_station_list[sim_station_list['ChargeDeviceId'] == chosen_station].head(1))
            # station_name = station_info['ChargeDeviceName'].values[0]
            charge_time = ev['ChargeTime']
            car_id = ev['CarId']
            resource = station_info['Station'].values[0]
            env.process(sim.car(env,car_id,chosen_station,resource,charge_time,now,log_df))
        env.run()
        # log_df.to_csv('simulation/output/log/mult_'+datetime.now().strftime("%Y%m%d%H%M")+str(i)+'_sim_result.log')
        # log_df.to_csv('simulation/sys_files/latest_sim_result.csv')
        sim_result = pd.concat([sim_result, log_df])
    sim_result.to_csv('simulation/output/log/mult_'+datetime.now().strftime("%Y%m%d%H%M")+'_sim_result.csv', index=False)
    print('file saved at '+'simulation/output/log/mult_'+datetime.now().strftime("%Y%m%d%H%M")+'_sim_result.csv')

# print(log_df)
x = dpr.cost_estimation(business_ref_table, 51.500095276686366, -2.5484000756829457)
print(json.dumps(x, indent=4, separators=(". ", " = ")))

