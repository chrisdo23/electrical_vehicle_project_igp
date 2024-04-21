import pandas as pd
import numpy as np
import random
import simpy
import simpy.rt as srt
import random
from datetime import datetime, timedelta
import data_processing as dpr
import library.config as cfg

# combined_hour_data = dpr.extract_traffic_data()
# station_data_simulation = dpr.extract_station_data(7)
# ports_data = dpr.extract_charging_port_data()
# take the file from offline sources
combined_hour_data = pd.read_csv('simulation/sys_files/generated_file/traffic_allocation.csv')
station_data_simulation = pd.read_csv('simulation/sys_files/generated_file/station_data_simulation.csv')
ports_data = pd.read_csv('simulation/sys_files/generated_file/ports_data.csv')


def car(env, car_id, chosen_station, resource, charge_time, now_time, log_df):
    arrival_hour = random.choices(population=combined_hour_data['hour'].values, weights=combined_hour_data['AverageTrafficCount'].values, cum_weights=None, k=1)[0]
    arrival_minute = arrival_hour*60*60 + random.randint(-30*60, 30*60)
    # trip_duration = random.randint(20, 60*24)
    wait_duration = random.randint(30*60, 60*60*2)
    
    # print('%s: Car id %s start driving' % (now_time + timedelta(minutes=int(env.now)), car_id))
    yield env.timeout(arrival_minute)
    # print('%s: Car id %s arrives at charging station \"%s\"' % (now_time + timedelta(minutes=int(env.now)), car_id, chosen_station))
    with resource.request() as req:
        if len(resource.queue) > 0:
            # print('%s: Car id %s arrives and starts queueing at station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
            write_event(log_df, 'arrive - queue', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)))
        yield req | env.timeout(wait_duration)
        if not req.triggered:
            # print('%s: Car id %s gives up on waiting at station \"%s\" after %d minutes' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station, wait_duration/60))
            write_event(log_df, 'queue - give up', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)))
        else:
            # Charge the battery        
            # print('%s: Car id %s arrives and starts to charge at station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
            write_event(log_df, 'arrive - charge', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)))
            yield env.timeout(charge_time)
            # print('%s: Car id %s finishes and leaves station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
            write_event(log_df, 'charge - finish', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)))

# log_df = pd.DataFrame(columns=['timestamp', 'car_id', 'station_id', 'event_name'])
def write_event(log_df, event_name, car_id, station_id, timestamp):
    log_df.loc[len(log_df.index)] = [timestamp, car_id, station_id, event_name]  

def generate_car_list():
    car_list = pd.DataFrame(list(range(0,cfg.user_per_day)), columns=['CarId'])
    car_list['ChargeType'], car_list['ChargeTime'] = zip(*car_list.apply(lambda x: dpr.charging_type_rand(ports_data), axis=1))
    car_list['StationId'] = car_list.apply(lambda x: dpr.charger_allocation(station_data_simulation), axis=1)
    car_list = car_list.merge(station_data_simulation, how='left', left_on=['StationId'], right_on=['ChargeDeviceId'])
    return car_list

def generate_staion(env):
    sim_station_list = []
    for i, station in station_data_simulation.iterrows():
        sim_station_list = sim_station_list + [{'ChargeDeviceId': station['ChargeDeviceId'],
                                                'ChargeDeviceName': station['ChargeDeviceName'], 
                                                'Station': simpy.Resource(env, capacity=station['ConnectorCount'])}]
    sim_station_list = pd.DataFrame(sim_station_list)
    return sim_station_list