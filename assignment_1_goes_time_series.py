import sunpy.timeseries as ts
from sunpy.net import Fido, attrs as a
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def get_time_window(timestamp, time_window_minutes):
    """
    Calculate the start and end times based on the given timestamp and time window.
    """
    delta = timedelta(minutes=time_window_minutes)
    start_time = timestamp - delta
    end_time = timestamp + delta
    return start_time, end_time

def fetch_satellite_data(start_time, end_time):
    """
    Fetch GOES satellite data using the specified time range.
    """
    result = Fido.search(a.Time(start_time, end_time), a.Instrument("XRS"),
                         a.goes.SatelliteNumber(15), a.Resolution("flx1s"))
    print(result)
    files = Fido.fetch(result)
    combined_ts = ts.TimeSeries(files, source='XRS', concatenate=True)
    return combined_ts

def plot_time_series(time_series, start_time, end_time, highlight_time):
    """
    Plot the time series data within the specified time range. Then highlight
    the timestamp.
    """
    time_series_trunc = time_series.truncate(start_time, end_time)
    fig, ax = plt.subplots()
    time_series_trunc.plot(axes=ax)
    ax.axvline(highlight_time, color='steelblue', linewidth=1.5, label="t={}".format(highlight_time))
    ax.legend()
    plt.show()


def main():
    timestamp_str = str(input("Please enter time stamp: "))
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")

    time_window_minutes = int(input("Enter a time window in minutes: "))
    if time_window_minutes <= 0:
        raise ValueError("The time window must be a positive integer.")
        
    start_time, end_time = get_time_window(timestamp, time_window_minutes)
    goes_ts = fetch_satellite_data(start_time, end_time)
    plot_time_series(goes_ts, start_time, end_time, timestamp)


main()