# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sunpy.timeseries as ts
from sunpy.net import Fido, attrs as a
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def get_time_window(timestamp, time_window_minutes):
    delta = timedelta(minutes=time_window_minutes)
    #perhaps we need to half it?
    start_time = timestamp - delta
    end_time = timestamp + delta
    
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M")
    
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M")
    return start_time_str, end_time_str

def fetch_satellite_data(start_time, end_time):
    # time_range = a.Time(start_time, end_time)
    
    # result = Fido.search(time_range, a.Instrument('XRS'))
    # if result.file_num == 0:
    #     raise ValueError("No files found for the given time range.")
     
    # file = Fido.fetch(result)
    # time_series = ts.TimeSeries(files, source='XRS', a.goes.SatelliteNumber(15), a.Resolution("flx1s")))
    result = Fido.search(a.Time(start_time, end_time), a.Instrument("XRS"), a.goes.SatelliteNumber(15), a.Resolution("flx1s"))
    print(result)
    file = Fido.fetch(result)
    time_series = ts.TimeSeries(file)
    
    return time_series

def plot_time_series(time_series):
    if time_series:
        time_series.peek()


def main():
    timestamp_str = "2017-12-21T15:41:59Z"
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
    
    time_window_minutes = int(input("Enter a time window in minutes. "))
    if time_window_minutes <= 0:
        raise ValueError("The time window must be a positive integer.")
        
    # start_time, end_time = get_time_window(timestamp, time_window_minutes)
    start_time, end_time = "2017-12-21 15:41","2017-12-21 16:11"
    goes_ts = fetch_satellite_data(start_time, end_time)
    plot_time_series(goes_ts)
    return 1

main()