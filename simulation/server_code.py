import pandas as pd
import numpy as np
import random
import simpy
import simpy.rt as srt
import random
from datetime import datetime, timedelta
import data_processing as dpr
import library.config as cfg

traffic_allocation = pd.read_csv('simulation/sys_files/generated_file/traffic_allocation.csv')
station_data_simulation = pd.read_csv('simulation/sys_files/generated_file/station_data_simulation.csv')
ports_data = pd.read_csv('simulation/sys_files/generated_file/ports_data.csv')
raw_station_data = pd.read_csv('simulation/sys_files/generated_file/raw_station_data.csv')
raw_hex_data = pd.read_csv('simulation/sys_files/generated_file/raw_hex_data.csv')

dpr.server_update_nearest_station(raw_hex_data, raw_station_data)
dpr.generate_business_data(raw_hex_data, raw_station_data)
