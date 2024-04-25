import pandas as pd
import numpy as np
import random
import h3
import os
# import folium     # for jupyter notebooks only
import library.mong_connection as mongo
import library.config as cfg
import library.g7_utility as ult
import asyncio

# Get MongoDB Data
## Predefined Queries
select_all = {}
select_bristol = {"ChargeDeviceLocation.Address.PostTown" : "Bristol"}
cwd = os.getcwd()


def query_from_collection(collection, query):
    project_db = mongo.get_database()
    collection_db = project_db[collection]
    result_list = mongo.mongo_query_to_list(collection_db, query)
    project_db.client.close()
    return result_list

def get_station_data(query):
    project_db = mongo.get_database()
    stations_collection = project_db['Stations']
    stations = mongo.mongo_query_to_list(stations_collection, query)

    # Setup simulation slate
    for station in stations:
        station['HexLevel'] = {}
        for res in range(5,10):
            station['HexLevel'][str(res)] = {'HexId' : h3.geo_to_h3(lat=float(station['ChargeDeviceLocation']['Latitude']),                                         
                                                                    lng=float(station['ChargeDeviceLocation']['Longitude']),
                                                                    resolution=res)}
        for connector in station['Connector']:
            connector['Status'] = False
            connector['LastUpdatedAt'] = None
    project_db.client.close()
    return stations

# Get hexagon data

def nearest_station(ref_hex_data, ref_station_data, db_station_list, lat, long, h3_res=7, min_station_count = 10, max_k_search = 10):
    # ref_hex_data: data by each hex
    # ref_station_data: data by each station
    # db_station_list: 'stations' list containing data of all stations
    # return [0]: list of result station details
    # return [1]: k number of the point
    station_count = 0
    k = 0
    while station_count < min_station_count and k <= max_k_search:    
        current_h3 = h3.geo_to_h3(lat, long, h3_res)
        h3_data = pd.DataFrame(h3.k_ring(current_h3, k), columns=['HexId'])
        h3_data['HexDistance'] = h3_data.apply(lambda x: h3.h3_distance(x['HexId'], current_h3), axis=1)
        h3_data = h3_data.merge(ref_hex_data, on = 'HexId', how = 'left').fillna(0)
        station_count = sum(h3_data['AreaStationCount'])
        k += 1
    h3_data = h3_data[h3_data['AreaStationCount'] > 0].sort_values(by=['HexDistance', 'AreaStationCount'],
                        ascending=[True, False])
    id_list = ref_station_data[ref_station_data['HexId'].isin(h3_data['HexId'])]
    result = [station for station in db_station_list if station['ChargeDeviceId'] in list(id_list['ChargeDeviceId'])]
    return result

def nearest_station_id(ref_hex_data, ref_station_data, lat, long, h3_res=7, min_station_count = 10, max_k_search = 10):
    station_count = 0
    k = 0
    while station_count < min_station_count and k <= max_k_search:    
        current_h3 = h3.geo_to_h3(lat, long, h3_res)
        h3_data = pd.DataFrame(h3.k_ring(current_h3, k), columns=['HexId'])
        h3_data['HexDistance'] = h3_data.apply(lambda x: h3.h3_distance(x['HexId'], current_h3), axis=1)
        h3_data = h3_data.merge(ref_hex_data, on = 'HexId', how = 'left').fillna(0)
        station_count = sum(h3_data['AreaStationCount'])
        k += 1
    h3_data = h3_data[h3_data['AreaStationCount'] > 0].sort_values(by=['HexDistance', 'AreaStationCount'],
                        ascending=[True, False])
    print(h3_data)
    id_list = ref_station_data[ref_station_data['HexId'].isin(h3_data['HexId'])]
    print(id_list)
    # result = [station for station in db_station_list if station['ChargeDeviceId'] in list(id_list['ChargeDeviceId'])]
    return id_list

def k_number(ref_hex_data, h3_hex, max_k_search = 10):
    print('searching for neighbor of ' + h3_hex)  
    station_count = 0
    k = 0
    while station_count == 0 and k <= max_k_search:  
        h3_data = list(h3.k_ring(h3_hex, k))
        # h3_data['HexDistance'] = h3_data.apply(lambda x: h3.h3_distance(x['HexId'], h3_hex), axis=1)
        # h3_data = h3_data.merge(ref_hex_data, on = 'HexId', how = 'left').fillna(0)
        comparison = ref_hex_data[ref_hex_data['HexId'].isin(h3_data)]
        station_count = sum(comparison['AreaStationCount'])
        k += 1
    if station_count > 0:
        k = k - 1
        print('found neighbors of ' + h3_hex + ' with ' + str(k))    
    else:
        k = None
        print('NOT found neighbors of ' + h3_hex)    
    return k, station_count

def centroid_coor(hex_code):
    vertices = h3.h3_to_geo_boundary(hex_code)
    centroid_lat = sum(point[0] for point in vertices) / len(vertices)
    centroid_lon = sum(point[1] for point in vertices) / len(vertices)
    return [centroid_lat, centroid_lon]

        # Test code for function
        # lat and long of UWE library

        # lat = 51.500095276686366
        # long = -2.5484000756829457

        # h3_data = nearest_station_id(lat, long, 7)

stations = get_station_data(select_bristol)
flatten_station_data = pd.json_normalize(stations, errors='raise', sep='.', max_level=None)
raw_traffic_data = pd.read_csv(cwd+'/simulation/sys_files/bristol_traffic_density.csv')

# Process traffic data

def process_traffic_data(simulation_res = -1):
    groupped_traffic_data = raw_traffic_data.groupby(['Count_point_id',
                                              'Region_id',
                                              'Region_name',
                                              'Region_ons_code', 
                                              'Local_authority_id',
                                              'Local_authority_name', 
                                              'Local_authority_code', 
                                              'Road_name',
                                              'Road_category', 
                                              'Road_type', 
                                              'Latitude',
                                              'Longitude',
                                              # 'Pedal_cycles',
                                              # 'Two_wheeled_motor_vehicles', 
                                              # 'Cars_and_taxis', 
                                            #   'Buses_and_coaches',
                                            #   'LGVs', 
                                            #   'HGVs_2_rigid_axle', 
                                            #   'HGVs_3_rigid_axle',
                                            #   'HGVs_4_or_more_rigid_axle', 
                                            #   'HGVs_3_or_4_articulated_axle',
                                            #   'HGVs_5_articulated_axle', 
                                            #   'HGVs_6_articulated_axle', 
                                            #   'All_HGVs',
                                            ], 
                                              as_index=False)['All_motor_vehicles'].mean()
    raw_station_data = pd.DataFrame()
    raw_station_data['_id'] = flatten_station_data['_id']
    raw_station_data['ChargeDeviceId'] = flatten_station_data['ChargeDeviceId']
    raw_station_data['ChargeDeviceName'] = flatten_station_data['ChargeDeviceName']
    raw_station_data['DateCreated'] = flatten_station_data['DateCreated']
    raw_station_data['Longitude'] = flatten_station_data['ChargeDeviceLocation.Longitude']
    raw_station_data['Latitude'] = flatten_station_data['ChargeDeviceLocation.Latitude']
    raw_station_data['Connector'] = flatten_station_data['Connector']
    raw_station_data['ConnectorCount'] = raw_station_data.apply(lambda x: len(list(x['Connector'])),1)

    traffic_data = pd.DataFrame()
    station_data = pd.DataFrame()
    all_hex_bristol = pd.DataFrame()

    if simulation_res < 0:
        min_res = cfg.min_res   
        max_res = cfg.max_res
    else:
        min_res = simulation_res  
        max_res = simulation_res

    for res in range(min_res,max_res+1):
        temp = groupped_traffic_data.copy()
        temp['HexLevel'] = res
        temp['HexId']= temp.apply(lambda x: h3.geo_to_h3(lat=float(x['Latitude']),                                    
                                                        lng=float(x['Longitude']),
                                                        resolution=res), 1)
        traffic_data = pd.concat([traffic_data, temp])
        

        temp = raw_station_data.copy()
        temp['HexLevel'] = res
        temp['HexId']= temp.apply(lambda x: h3.geo_to_h3(lat=float(x['Latitude']),                                    
                                                        lng=float(x['Longitude']),
                                                        resolution=res), 1)
        station_data = pd.concat([station_data, temp])

        temp = pd.DataFrame(h3.polyfill(cfg.geo_json_polygon, res), columns=['HexId'])
        temp['HexLevel'] = res
        all_hex_bristol = pd.concat([all_hex_bristol, temp])

    traffic_data = ult.to_camel_case(traffic_data)
    station_data = ult.to_camel_case(station_data)
    all_hex_bristol = ult.to_camel_case(all_hex_bristol)
    hex_traffic_data = (traffic_data
                        .groupby(['HexLevel', 'HexId'], as_index=False)
                        .agg(
                            AverageMotorVehicles = ('AllMotorVehicles', 'mean')
                        ))
    hex_station_data = (station_data
                        .groupby(['HexLevel', 'HexId'], as_index=False)
                        .agg(
                            AreaConnectorCount = ('ConnectorCount', 'sum'),
                            AreaStationCount = ('Id', 'count')
                        ))
    aggregated_hex_data = (all_hex_bristol
                        .merge(hex_traffic_data, how='left', on=['HexId', 'HexLevel'])
                        .merge(hex_station_data, how='left', on=['HexId', 'HexLevel'])
                        .fillna(0))
    raw_hex_data = aggregated_hex_data.copy()
    raw_hex_data['CentroidCoor'] = raw_hex_data.apply(lambda x: centroid_coor(x['HexId']), axis=1)
    # Extremely slow: 1m17s
    raw_hex_data['KNumber'] = raw_hex_data.apply(lambda x: k_number(aggregated_hex_data, x['HexId'], 30)[0], axis=1)

    return station_data, raw_hex_data


# data_by_station, data_by_hex = process_traffic_data()
# nearest_station_id(data_by_hex, data_by_station, 51.500095276686366, -2.5484000756829457)
# nearest_station(data_by_hex, data_by_station, stations, 51.500095276686366, -2.5484000756829457)

async def server_update_nearest_station(data_by_hex, data_by_station):    
    project_db = mongo.get_database()
    location_db = project_db['current_location']
    response_db = project_db['python_response_nearest_stations']
    # while True:
    # Query location from current_location
    location_json = location_db.find_one({}, sort=[('timestamp', -1)])
    # Delete all data in python_response_nearest_stations
    response_db.delete_many({})
    # Run nearest station calculation
    data = nearest_station(data_by_hex, data_by_station, 
                           stations, 
                           float(location_json['car_location']['Latitude']), 
                           float(location_json['car_location']['Longitude']))
    # Push to python_response_nearest_stations
    response_db.insert_many(data)
    # await asyncio.sleep(30)
    project_db.client.close()

def generate_business_data(raw_hex_data, raw_station_data):
    # raw_hex_data
    avg_traffic_per_hexagon = (raw_hex_data.copy()
                            .query('AverageMotorVehicles > 0')
                            .groupby(['HexLevel'], as_index=False)
                            .agg(
                                AverageMotorVehiclesPerHex = ('AverageMotorVehicles', 'mean')
                            ))

    avg_daily_demand_per_station = cfg.user_per_day/raw_station_data['ChargeDeviceId'].count()
    # avg_traffic_per_hexagon
    # test['']
    avg_traffic_per_hexagon
    # CAR PER HOUR
    # place have 400 cars per hour --> ratio 400/270 --> mult with the average demand (which is two per station)
    business_ref_table = raw_hex_data.copy()
    business_ref_table = pd.merge(business_ref_table, avg_traffic_per_hexagon, how='left', on=['HexLevel'])
    business_ref_table['IniCostHardwareCost'] = 1000
    business_ref_table['IniCostInstallationCost'] = 400
    business_ref_table['IniGridReinforcementCost'] = business_ref_table['KNumber'].apply(lambda x: 0 if x <= 1 else 500000)
    business_ref_table['DailyDemandPerStation'] = business_ref_table.apply(lambda x: avg_daily_demand_per_station * x['AverageMotorVehicles'] / x['AverageMotorVehiclesPerHex'], axis=1)
    business_ref_table['DailyElectricityCost'] = business_ref_table['DailyDemandPerStation']*1.74312
    business_ref_table['DailyEstimatedRevenue'] = business_ref_table['DailyDemandPerStation']*26
    business_ref_table['MonthlyEstimatedRevenue'] = business_ref_table['DailyEstimatedRevenue']*30
    business_ref_table['MonthlyElectricityCost'] = business_ref_table['DailyElectricityCost']*30
    business_ref_table['MonthlyMaintenanceCost'] = 300
    return business_ref_table

# if k number < 2 --> Maybe the grid reinforcement has been paid
# need to recheck
def cost_estimation(business_ref_table, lat, long, charge_point = 1, rental_cost = 2000, hex_res = 7):
    ref_data = business_ref_table.copy().query('HexLevel == @hex_res')
    h3_address = h3.geo_to_h3(lat, long, hex_res)
    result = ref_data[ref_data['HexId'] == h3_address]
    if result.empty:
        result = {'Error' : 'Outside of search range'}
    else:
        result['Base Area'] = h3.hex_area(hex_res)
        result['Charging Station In Area'] = result['AreaStationCount']
        result['Charging Anxiety Level'] = result['KNumber'].apply(lambda x: 'Low' if x <= 1 else ('Medium' if (x>1 and x<3) else 'High'))
        result['Daily Demand'] = round(result['DailyDemandPerStation'], 2)
        result['Chargepoint Hardware Costs'] = result['IniCostHardwareCost']*charge_point
        result['Chargepoint Installation Costs'] = result['IniCostInstallationCost']*charge_point
        result['Grid Reinforcement Costs'] = result['IniGridReinforcementCost']
        result['Electricity Cost'] = result['MonthlyElectricityCost']
        result['Maintenance Cost'] = result['MonthlyMaintenanceCost']
        result['Property Rental'] = rental_cost
        result['Estimated Revenue'] = result['MonthlyEstimatedRevenue']
        result['Estimated Profit'] = result['Estimated Revenue'] - result['Electricity Cost'] - result['Maintenance Cost'] - result['Property Rental']
        result['Initial Cost'] = result['Chargepoint Hardware Costs'] + result['Chargepoint Installation Costs'] + result['Grid Reinforcement Costs']
        result['Break Even (Years)'] = result['Initial Cost']/result['Estimated Profit']

        cost_analysis = result[['Base Area', 
                                'Charging Station In Area', 
                                'Charging Anxiety Level', 
                                'Daily Demand', 
                                'Chargepoint Hardware Costs',
                                'Chargepoint Installation Costs',
                                'Grid Reinforcement Costs',
                                'Electricity Cost',
                                'Maintenance Cost',
                                'Property Rental',
                                'Estimated Revenue',
                                'Estimated Profit',
                                'Initial Cost',
                                'Break Even (Years)']].head(1).copy()
        return cost_analysis.to_dict('records')

async def server_update_business_db(business_ref_table):    # NEED TO RREPLACE NEW FUNCTION
    project_db = mongo.get_database()
    request_db = project_db['business_request']
    response_db = project_db['business_response']
    # while True:
    # Query location from current_location
    request_json = request_db.find_one({}, sort=[('timestamp', -1)])
    # Delete all data in python_response_nearest_stations
    response_db.delete_many({})
    # Run nearest station calculation
    data = cost_estimation(business_ref_table, 
                           float(request_json['latitude']),
                           float(request_json['longitude']))
    # Push to python_response_nearest_stations
    response_db.insert_many(data)
    # await asyncio.sleep(30)
    # await asyncio.sleep(30)
    project_db.client.close()

# Simulation Preparation
## Time allocation

def extract_traffic_data(dfactor = 0.5):
    # dfactỏ - Arbitrary factor for scaling down traffic after woking hours
    # group by hour, calculate mean, std of traffic
    traffic_by_hour = raw_traffic_data[raw_traffic_data['Year'] == 2022].groupby(['Year', 'hour'], as_index=False).agg(
        AverageTrafficCount = ('All_motor_vehicles', 'median')
    )
    traffic_by_hour
    traffic_7am = traffic_by_hour[traffic_by_hour['hour'] == 7]['AverageTrafficCount'].values[0]
    traffic_6pm = traffic_by_hour[traffic_by_hour['hour'] == 18]['AverageTrafficCount'].values[0]
    missing_hour = pd.DataFrame({'Year': [2022,2022,2022,2022,2022,2022,2022,2022,2022,2022,2022,2022],
                                'hour': [1,2,3,4,5,6,19,20,21,22,23,24],
                                'AverageTrafficCount': [traffic_7am*dfactor**6, 
                                                        traffic_7am*dfactor**5, 
                                                        traffic_7am*dfactor**4, 
                                                        traffic_7am*dfactor**3, 
                                                        traffic_7am*dfactor**2, 
                                                        traffic_7am*dfactor,
                                                        traffic_6pm*dfactor**2,
                                                        traffic_6pm*dfactor**3,
                                                        traffic_6pm*dfactor**4,
                                                        traffic_6pm*dfactor**5,
                                                        traffic_6pm*dfactor**6,
                                                        traffic_6pm*dfactor**7]})

    combined_hour_data = pd.concat([traffic_by_hour, missing_hour])
    combined_hour_data = combined_hour_data.sort_values(by=['hour'], ascending=[True])
    return combined_hour_data

# For individual dates
def extract_traffic_data_by_date(date, dfactor = 0.5, traffic_count_data=raw_traffic_data):
    # dfactor - Arbitrary factor for scaling down traffic after woking hours
    # group by hour, calculate mean, std of traffic

    traffic_by_hour = traffic_count_data.query('CountDate==@date').groupby(['Year','hour'], as_index=False).agg(
        AverageTrafficCount = ('AllMotorVehicles', 'median')
    )
    traffic_by_hour
    traffic_7am = traffic_by_hour[traffic_by_hour['hour'] == 7]['AverageTrafficCount'].values[0]
    traffic_6pm = traffic_by_hour[traffic_by_hour['hour'] == 18]['AverageTrafficCount'].values[0]
    missing_hour = pd.DataFrame({'Year': [2022,2022,2022,2022,2022,2022,2022,2022,2022,2022,2022,2022],
                                'hour': [1,2,3,4,5,6,19,20,21,22,23,24],
                                'AverageTrafficCount': [traffic_7am*dfactor**6, 
                                                        traffic_7am*dfactor**5, 
                                                        traffic_7am*dfactor**4, 
                                                        traffic_7am*dfactor**3, 
                                                        traffic_7am*dfactor**2, 
                                                        traffic_7am*dfactor,
                                                        traffic_6pm*dfactor**2,
                                                        traffic_6pm*dfactor**3,
                                                        traffic_6pm*dfactor**4,
                                                        traffic_6pm*dfactor**5,
                                                        traffic_6pm*dfactor**6,
                                                        traffic_6pm*dfactor**7]})

    combined_hour_data = pd.concat([traffic_by_hour, missing_hour])
    combined_hour_data = combined_hour_data.sort_values(by=['hour'], ascending=[True])
    return combined_hour_data

def extract_charging_port_data():
    ports_data = []
    for station in stations:
        ports_data = ports_data + station['Connector']
    # ports_data = pd.DataFrame(ports_data)
    ports_data_df = pd.DataFrame(ports_data)
    # type(stations[1]['Connector'])
    agg_ports_data = ports_data_df.groupby(['ConnectorType'], as_index=False).count()
    return agg_ports_data

def extract_station_data(simulation_res = 7):
    station_data, raw_hex_data = process_traffic_data()
    hex_data_simulation = raw_hex_data[raw_hex_data['HexLevel'] == simulation_res].copy()
    # hex_data_simulation
    station_data_simulation = station_data[station_data['HexLevel'] == simulation_res].copy()
    station_data_simulation = station_data_simulation.merge(hex_data_simulation, how='left', on=['HexId', 'HexLevel'])
    station_data_simulation['AverageMotorVehicles'] = station_data_simulation['AverageMotorVehicles'].fillna(0) + 1
    return station_data_simulation

## Randomizer

def charging_type_rand(ref_agg_port_data):
    charge_type = random.choices(ref_agg_port_data['ConnectorType'], weights=ref_agg_port_data['ConnectorId'], cum_weights=None, k=1)[0]
    if 'CHAdeMO' in charge_type:
        charge_time = random.randint(20*60, 80*60)
    elif 'CCS' in charge_type:
        charge_time = random.randint(20*60, 80*60)
    elif 'Mennekes' in charge_type:
        charge_time = random.randint(60*60, 60*60*6)
    elif 'BS1363' in charge_type:
        charge_time = random.randint(60*60, 60*60*6)
    else:
        charge_time = random.randint(20*60, 60*60*6)
    return charge_type, charge_time

def charger_allocation(ref_station_data):
    station_id = random.choices(ref_station_data['ChargeDeviceId'], weights=ref_station_data['AverageMotorVehicles'], cum_weights=None, k=1)[0]
    return station_id

## Generate simulation data

