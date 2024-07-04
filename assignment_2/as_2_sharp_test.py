import sunpy.map as map
from sunpy.net import Fido, attrs as a
import matplotlib.pyplot as plt
import astropy.units as u
from datetime import datetime, timedelta
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np
import sunpy.timeseries as ts
from sunkit_instruments import goes_xrs
from sunpy.time import TimeRange

def get_time_and_window():
    """
    Obtain and validate a single timestamp and a time window in minutes.
    """
    print("You can enter a date or timestamp in various formats such as:")
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
    Converts timestamp string into datetime object. Handles multiple
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

def get_time_window(timestamp, time_window_minutes):
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
        result = Fido.search(a.Time(start_time, end_time), a.Instrument("XRS"))
        files = Fido.fetch(result)
        combined_ts = ts.TimeSeries(files, source='XRS', concatenate=True)
        return combined_ts
    except:
        raise RuntimeError("Failed to fetch GOES data or data does not exist.")

def plot_goes_time_series(time_series, start_time, end_time, highlight_time):
    """
    Plot the GOES time series data within the specified time range. Then highlight
    the timestamp.
    """
    time_series_trunc = time_series.truncate(start_time, end_time)
    fig, ax = plt.subplots()
    time_series_trunc.plot(axes=ax)
    ax.axvline(highlight_time, color='steelblue', linewidth=1.5, label="t={}".format(highlight_time))
    ax.legend()
    ax.set_title("GOES X-Ray Flux")
    plt.show()

def fetch_harpnums(timestamp):
    """
    Fetch available HARPNUMs for the given timestamp.
    """
    print(f"Fetching available HARPNUMs for {timestamp}...")
    search_result = Fido.search(a.Time(timestamp, timestamp),
                                a.jsoc.Series("hmi.sharp_720s"))
    harpnums = {record["HARPNUM"] for record in search_result[0]}
    print("Available HARPNUMs:", sorted(harpnums))
    return sorted(harpnums)

def select_harpnum(available_harpnums):
    """
    Prompt the user for a valid HARPNUM from the available options.
    """
    while True:
        harpnum = input(f"Enter HARPNUM from available options (or press Enter to fetch data for all active regions): ").strip()
        if harpnum == "":
            return None
        try:
            harpnum = int(harpnum)
            if harpnum in available_harpnums:
                return harpnum
            else:
                print(f"Invalid HARPNUM. Please enter one of the available options: {available_harpnums}")
        except ValueError:
            print(f"Invalid input. Please enter a valid HARPNUM from the available options: {available_harpnums}")

def fetch_aarp_data(filepath):
    # Temporary manual download of AARP data
    return None

def fetch_sharp_data(timestamp, harpnum=None):
    """
    Fetch SHARP data from JSOC.
    """
    jsoc_email = str(input("Please enter an email registered with JSOC: "))
    if harpnum:
        sharp_result = Fido.search(a.Time(timestamp, timestamp),
                                   a.Sample(1*u.hour),
                                   a.jsoc.Series("hmi.sharp_cea_720s"),
                                   a.jsoc.PrimeKey("HARPNUM", harpnum),
                                   a.jsoc.Notify(jsoc_email),
                                   a.jsoc.Segment('magnetogram'))
    else:
        sharp_result = Fido.search(a.Time(timestamp, timestamp),
                                   a.Sample(1*u.hour),
                                   a.jsoc.Series("hmi.sharp_cea_720s"),
                                   a.jsoc.Notify(jsoc_email),
                                   a.jsoc.Segment('magnetogram'))
    files = Fido.fetch(sharp_result)
    sharp_maps = map.Map(files)
    return sharp_maps


def fix_metadata(sharp_maps):
    """
    Fix metadata issues for SHARP maps.
    """
    if isinstance(sharp_maps, list):
        for smap in sharp_maps:
            if "bunit" in smap.meta and smap.meta["bunit"] == "Mx/cm^2":
                smap.meta["bunit"] = r"Mx cm$^{-2}$"
    else:
        if "bunit" in sharp_maps.meta and sharp_maps.meta["bunit"] == "Mx/cm^2":
            sharp_maps.meta["bunit"] = r"Mx cm$^{-2}$"
    return sharp_maps

def plot_combined_data(sharp_map, aarp_filepaths, goes_ts, start_time, end_time, highlight_time):
    fig = plt.figure(figsize=(15, 10))
    
    # Plot SHARP data with its WCS projection
    ax1 = fig.add_subplot(221, projection=sharp_map)
    im1 = ax1.imshow(sharp_map.data, cmap='afmhot', origin='lower')
    harpnum = sharp_map.meta.get('HARPNUM')
    sharp_time = sharp_map.date
    sharp_unit = sharp_map.meta.get('bunit', 'Unknown')
    sharp_x_unit = sharp_map.meta.get('cunit1', 'degree')
    sharp_y_unit = sharp_map.meta.get('cunit2', 'degree')
    ax1.set_title(f"SHARP - {harpnum} at {sharp_time}")
    ax1.set_xlabel(f"CEA Longitude ({sharp_x_unit})")
    ax1.set_ylabel(f"CEA Latitude ({sharp_y_unit})")
    cb1 = plt.colorbar(im1, ax=ax1, label=sharp_unit)
    
    # Plot AARP data with adjusted vmin and vmax
    for i, filepath in enumerate(aarp_filepaths):
        with fits.open(filepath) as hdul:
            ext = hdul[1]
            time_key = f"T_IMG05"
            specific_time = ext.header.get(time_key, 'Unknown')
            wavelength = ext.header.get('WAVELNTH', 'Unknown')
            data = ext.data[5, :, :]

            # Extract WCS information from the header
            wcs = WCS(ext.header, naxis=2)
            ax = fig.add_subplot(2, 2, i+2, projection=wcs)
            
            # Calculate vmin and vmax for better dynamic range
            vmin = np.percentile(data, 1)
            vmax = np.percentile(data, 99.5)

            im = ax.imshow(data, cmap='afmhot', origin='lower', aspect='auto', vmin=vmin, vmax=vmax)
            aarp_x_unit = ext.header.get('CUNIT1', 'Unknown')
            aarp_y_unit = ext.header.get('CUNIT2', 'Unknown')
            unit = ext.header.get('BUNIT', 'Intensity')  # Get unit for colorbar from header if available
            ax.coords[0].set_axislabel(f'Solar X ({aarp_x_unit})')
            ax.coords[1].set_axislabel(f'Solar Y ({aarp_y_unit})')
            ax.set_title(f'AARP - {wavelength} Å at {specific_time}')
            plt.colorbar(im, ax=ax, label=unit)
    
    # Plot GOES data in the 2x2 grid
    ax4 = fig.add_subplot(224)
    goes_ts_trunc = goes_ts.truncate(start_time, end_time)
    goes_ts_trunc.plot(axes=ax4)
    ax4.axvline(highlight_time, color='steelblue', linewidth=1.5, label="t={}".format(highlight_time))
    ax4.legend()
    ax4.set_title("GOES X-Ray Flux")
    
    plt.tight_layout()
    plt.show()


def main():
    timestamp, time_window_minutes = get_time_and_window()
    start_time, end_time = get_time_window(timestamp, time_window_minutes)
    available_harpnums = fetch_harpnums(timestamp)
    harpnum = select_harpnum(available_harpnums)

    try:
        print(f"Fetching SHARP data for {timestamp}...")
        sharp_maps = fetch_sharp_data(timestamp, harpnum)
        sharp_maps = fix_metadata(sharp_maps)
        print("SHARP data fetched successfully. Plotting the data...")

        print(f"Fetching GOES data from {start_time} to {end_time}...")
        goes_ts = fetch_goes_data(start_time, end_time)
        print("GOES data fetched successfully. Plotting the data...")

        aarp_filepaths = [
            r"C:\Users\vaina\OneDrive\Documents\Kerala Internship\assignment_2\AARP fits files\2011.05.28_15 48 00_7h@1h_AARP625_171.fits",
            r"C:\Users\vaina\OneDrive\Documents\Kerala Internship\assignment_2\AARP fits files\2011.05.28_15 48 00_7h@1h_AARP625_304.fits"
        ]

        plot_combined_data(sharp_maps, aarp_filepaths, goes_ts, start_time, end_time, timestamp)
        print("Plot displayed successfully.")
    except RuntimeError as fetch_error:
        print(fetch_error)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
