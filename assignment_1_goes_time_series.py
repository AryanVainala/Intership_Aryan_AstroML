import sunpy.timeseries as ts
from sunpy.net import Fido, attrs as a
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

def get_time_and_window():
    """
    Obtain and validate a single timestamp and a time window in minutes.
    """
    print("You can enter a date or timestamp in various formats such as :")
    print("-----------------------------------------------------")
    print("- YYYY-MM-DDThh:mm:ssZ")
    print("- YYYY-MM-DD hh:mm:ss")
    print("- YYYY-MM-DD")
    print("- DD-MM-YYYY")
    print("- MM/DD/YYYY")
    print("- YYYY/MM/DD")
    print("- DD Month YYYY")
    print("- Month DD, YYYY")
    print("-----------------------------------------------------")

    while True:
        try:
            timestamp_str = str(input("Please enter time stamp: "))
            timestamp = time_convert(timestamp_str)
            break
        except ValueError as e:
            print(e)

    while True:
        try:
            time_window_minutes = int(input("Enter a time window in minutes: "))
            if time_window_minutes <= 0:
                raise ValueError("The time window must be a positive integer.")
            break
        except ValueError:
            print("Error: Please enter a valid integer.")

    return timestamp, time_window_minutes

def time_convert(timestamp_str):
    """
    Converts timestamp string into datetime objecct. Handles multiple
    formats for improved user interface.
    """
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d %B %Y",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except:
            pass
    raise ValueError("Invalid date/timestamp format. Please try again.")

def get_start_and_end_time(timestamp, time_window_minutes):
    """
    Calculate the start and end times based on the given timestamp and time window.
    """
    delta = timedelta(minutes=time_window_minutes)
    start_time = timestamp - delta
    end_time = timestamp + delta
    return start_time, end_time

def fetch_goes_data(start_time, end_time):
    """
    Fetch GOES satellite data using the specified time range.
    """
    try:
        result = Fido.search(a.Time(start_time, end_time), a.Instrument("XRS"),
                             a.Resolution("flx1s"))
        
        # Select data from the latest satellite
        responses = result['xrs']
        satellite_filter_index = int(np.argmax(responses["SatelliteNumber"]))
        files = Fido.fetch(result[0,satellite_filter_index:])
        combined_ts = ts.TimeSeries(files, source='XRS', concatenate=True)
        time_series_trunc = combined_ts.truncate(start_time, end_time)
        return time_series_trunc
    except:
        raise RuntimeError("Failed to fetch Satellite data or data does not exist.")

def plot_time_series(time_series, highlight_time):
    """
    Plot the time series data within the specified time range. Then highlight
    the timestamp.
    """
    
    fig, ax = plt.subplots()
    time_series.plot(axes=ax)
    ax.axvline(highlight_time, color='steelblue', linewidth=1.5, label="t={}".format(highlight_time))
    ax.legend()
    ax.set_title("GOES X-Ray Flux")
    plt.show()


def main():
    timestamp, time_window_minutes = get_time_and_window()
    try:
        start_time, end_time = get_start_and_end_time(timestamp, time_window_minutes)
        print(f"Fetching data from {start_time} to {end_time}...")
        goes_ts = fetch_goes_data(start_time, end_time)
        print("Data fetched successfully. Plotting the data...")
        plot_time_series(goes_ts, timestamp)
        print("Plot displayed successfully.")
    except RuntimeError as fetch_error:
        print(fetch_error)
    except Exception as e:
        print(f"An error occurred while plotting the data: {e}")

if __name__ == "__main__":
    main()