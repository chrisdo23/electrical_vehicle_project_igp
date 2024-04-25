import pandas as pd
import numpy as np
import random
import simpy
import simpy.rt as srt
import random
from random import choices
from string import ascii_lowercase
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


def car(env, car_id, chosen_station, resource, charge_time, now_time, log_df, traffic_allocation=combined_hour_data):
    arrival_hour = random.choices(population=traffic_allocation['hour'].values, weights=traffic_allocation['AverageTrafficCount'].values, cum_weights=None, k=1)[0]
    arrival_second = arrival_hour*60*60 + random.randint(-30*60, 30*60)
    # trip_duration = random.randint(20, 60*24)
    wait_duration = random.randint(30*60, 60*60*2)
    
    # print('%s: Car id %s start driving' % (now_time + timedelta(minutes=int(env.now)), car_id))
    yield env.timeout(arrival_second)
    # print('%s: Car id %s arrives at charging station \"%s\"' % (now_time + timedelta(minutes=int(env.now)), car_id, chosen_station))
    with resource.request() as req:
        if len(resource.queue) > 0:     # If there is a queue
            # print('%s: Car id %s arrives and starts queueing at station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
            write_event(log_df, 'arrive - queue', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)), np.nan)
            yield req | env.timeout(wait_duration)
            if not req.triggered:
                # print('%s: Car id %s gives up on waiting at station \"%s\" after %d minutes' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station, wait_duration/60))
                write_event(log_df, 'queue - give up', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)), wait_duration)
            else:
                # From queue to charge the battery        
                # print('%s: Car id %s arrives and starts to charge at station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
                write_event(log_df, 'queue - charge', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)), env.now-arrival_second)
                yield env.timeout(charge_time)
                # print('%s: Car id %s finishes and leaves station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
                write_event(log_df, 'charge - finish', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)), charge_time)
        else:       # If no queue is needed
            # Charge the battery right away
            # print('%s: Car id %s arrives and starts to charge at station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
            write_event(log_df, 'arrive - charge', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)), np.nan)
            yield env.timeout(charge_time)
            # print('%s: Car id %s finishes and leaves station \"%s\"' % (now_time + timedelta(seconds=int(env.now)), car_id, chosen_station))
            write_event(log_df, 'charge - finish', car_id, chosen_station, now_time + timedelta(seconds=int(env.now)), charge_time)

# log_df = pd.DataFrame(columns=['timestamp', 'car_id', 'station_id', 'event_name'])
def write_event(log_df, event_name, car_id, station_id, timestamp, elapsed_value):
    log_df.loc[len(log_df.index)] = [timestamp, car_id, station_id, event_name, elapsed_value]  

def generate_car_list(user_per_day = cfg.user_per_day, station_data_simulation = station_data_simulation):
    car_list = pd.DataFrame(list(range(0, int(user_per_day))), columns=['CarId'])
    identifier = ''.join([random.choice(ascii_lowercase) for _ in range(3)])
    car_list['CarId'] = car_list['CarId'].apply(lambda x: identifier + '%04d' % x)
    car_list['ChargeType'], car_list['ChargeTime'] = zip(*car_list.apply(lambda x: dpr.charging_type_rand(ports_data), axis=1))
    car_list['StationId'] = car_list.apply(lambda x: dpr.charger_allocation(station_data_simulation), axis=1)
    car_list = car_list.merge(station_data_simulation, how='left', left_on=['StationId'], right_on=['ChargeDeviceId'])
    return car_list

def generate_staion(env, station_data_simulation=station_data_simulation):
    sim_station_list = []
    for i, station in station_data_simulation.iterrows():
        sim_station_list = sim_station_list + [{'ChargeDeviceId': station['ChargeDeviceId'],
                                                'ChargeDeviceName': station['ChargeDeviceName'], 
                                                'Station': simpy.Resource(env, capacity=station['ConnectorCount'])}]
    sim_station_list = pd.DataFrame(sim_station_list)
    return sim_station_list