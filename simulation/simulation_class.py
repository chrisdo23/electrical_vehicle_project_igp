# Lib import
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

# Car Object
class Vehicle():

    def __init__(self, ini_long = 0, ini_lat = 0, home_long = 0, home_lat = 0, port_type = "default"):
        self.long = ini_long
        self.lat = ini_lat
        self.home_long = home_long
        self.home_lat = home_lat
        self.port_type = port_type
        self.last_known_loc = []
        self.last_known_loc.append([datetime.now(timezone(timedelta(0))), ini_long, ini_lat])
        
    def pos_update(self, long, lat):
        # Add current location to last known position list. Ref below.
            # timezone_offset = -8.0  # Pacific Standard Time (UTC−08:00)
            # tzinfo = timezone(timedelta(hours=timezone_offset))
            # datetime.now(tzinfo)
        self.last_known_loc.append([datetime.now(timezone(timedelta(0))), long, lat])
        self.last_known_loc = self.last_known_loc[-50:]
        self.long = long
        self.lat = lat

    def home_update(self, long, lat):
        self.home_long = long
        self.home_lat = lat

# Hexagon Object
# 