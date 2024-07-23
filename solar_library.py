import sunpy.timeseries as ts
from sunpy.net import Fido, attrs as a
from datetime import datetime, timedelta
import matplotlib, matplotlib.pyplot as plt
import numpy as np
import sunpy.map as map
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
from sunkit_instruments import goes_xrs
from sunpy.time import TimeRange
import pandas as pd

def get_time_and_window():
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
    delta = timedelta(minutes=time_window_minutes)
    start_time = timestamp - delta
    end_time = timestamp + delta
    return start_time, end_time

def fetch_goes_data(start_time, end_time):
    try:
        print(f"Fetching data from {start_time} to {end_time}...")
        result = Fido.search(a.Time(start_time, end_time), a.Instrument("XRS"), a.Resolution("flx1s"))
        responses = result['xrs']
        satellite_filter_index = int(np.argmax(responses["SatelliteNumber"]))
        files = Fido.fetch(result[0,satellite_filter_index:])
        combined_ts = ts.TimeSeries(files, source='XRS', concatenate=True)
        time_series_trunc = combined_ts.truncate(start_time, end_time)
        print("GOES data fetched successfully...")
        return time_series_trunc
    except:
        raise RuntimeError("Failed to fetch Satellite data or data does not exist.")

def plot_time_series(time_series, highlight_time):
    fig, ax = plt.subplots()
    time_series.plot(axes=ax)
    ax.axvline(highlight_time, color='steelblue', linewidth=1.5, label="t={}".format(highlight_time))
    ax.legend()
    ax.set_title("GOES X-Ray Flux")
    plt.show()

def fetch_flare_events(start_time, end_time):
    flare_events = goes_xrs.get_goes_event_list(TimeRange(start_time, end_time))
    flare_df = pd.DataFrame(flare_events)
    return flare_df

def check_if_ar_flared(flare_df, noaa_numbers, timestamp):
    if flare_df.empty:
        return False
    
    if noaa_numbers.size == 0:
        print("NOAA numbers are missing cannot check if flare occured.")
    
    for noaa in noaa_numbers:
        flares_for_noaa = flare_df[flare_df['noaa_active_region'] == noaa]
        for _, flare in flares_for_noaa.iterrows():
            start_time = flare['start_time']
            end_time = flare['end_time']
            if start_time <= timestamp <= end_time:
                return True
    return False

def fetch_harpnums(timestamp):
    print(f"Fetching available HARPNUMs for {timestamp}...")
    search_result = Fido.search(a.Time(timestamp, timestamp),
                                a.jsoc.Series("hmi.sharp_720s"))
    harpnums = {record["HARPNUM"] for record in search_result[0]}
    print("Available HARPNUMs:", sorted(harpnums))
    return sorted(harpnums)

def select_harpnum(available_harpnums):
    while True:
        harpnum = input("Enter HARPNUM from available options (or press Enter to fetch data for all active regions): ").strip()
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
    return None

def fetch_sharp_data(timestamp, harpnum=None):
    jsoc_email = str(input("Please enter an email registered with JSOC: "))
    print(f"Fetching SHARP data for {timestamp}...")
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
    
    noaa_numbers = sharp_result[0]["NOAA_ARS"]
    noaa_string = noaa_numbers[0].item()
    
    if (noaa_string != 'MISSING') and (noaa_string is not None):
        noaa_num_array = np.array(noaa_string.split(','), dtype='int')
    else:
        noaa_num_array = np.array([])

    files = Fido.fetch(sharp_result)
    sharp_maps = map.Map(files)
    return sharp_maps, noaa_num_array

def fix_metadata(sharp_maps):
    if isinstance(sharp_maps, list):
        for smap in sharp_maps:
            if "bunit" in smap.meta and smap.meta["bunit"] == "Mx/cm^2":
                smap.meta["bunit"] = r"Mx cm$^{-2}$"
    else:
        if "bunit" in sharp_maps.meta and sharp_maps.meta["bunit"] == "Mx/cm^2":
            sharp_maps.meta["bunit"] = r"Mx cm$^{-2}$"
    return sharp_maps

def plot_combined_data(sharp_map, aarp_filepaths, goes_ts, highlight_time, flared):
    fig = plt.figure(figsize=(15, 10))
    
    ax1 = fig.add_subplot(221, projection=sharp_map)
    im1 = ax1.imshow(sharp_map.data, cmap='afmhot', origin='lower')
    harpnum = sharp_map.meta.get('HARPNUM')
    sharp_time = sharp_map.date
    sharp_unit = sharp_map.meta.get('bunit', 'Unknown')
    sharp_x_unit = sharp_map.meta.get('cunit1', 'degree')
    sharp_y_unit = sharp_map.meta.get('cunit2', 'degree')
    ax1.set_title(f"SHARP - {harpnum} at {sharp_time.iso} | AR flared - {flared}")
    ax1.set_xlabel(f"CEA Longitude ({sharp_x_unit})")
    ax1.set_ylabel(f"CEA Latitude ({sharp_y_unit})")
    plt.colorbar(im1, ax=ax1, label=sharp_unit)
    
    for i, filepath in enumerate(aarp_filepaths):
        with fits.open(filepath) as hdul:
            ext = hdul[1]
            time_key = f"T_IMG05"
            specific_time = ext.header.get(time_key, 'Unknown')
            aarp_wavelength = ext.header.get('WAVELNTH', 'Unknown')
            aarp_colormap = matplotlib.colormaps[f'sdoaia{aarp_wavelength}']
            data = ext.data[5, :, :]

            wcs = WCS(ext.header, naxis=2)
            ax = fig.add_subplot(2, 2, i+2, projection=wcs)
            
            vmin = np.percentile(data, 1)
            vmax = np.percentile(data, 99.5)

            im = ax.imshow(data, cmap=aarp_colormap, origin='lower', aspect='auto', vmin=vmin, vmax=vmax)
            aarp_x_unit = ext.header.get('CUNIT1', 'Unknown')
            aarp_y_unit = ext.header.get('CUNIT2', 'Unknown')
            unit = ext.header.get('BUNIT', 'Intensity')
            ax.coords[0].set_axislabel(f'Solar X ({aarp_x_unit})')
            ax.coords[1].set_axislabel(f'Solar Y ({aarp_y_unit})')
            ax.set_title(f'AARP - {aarp_wavelength} Å at {specific_time}')
            plt.colorbar(im, ax=ax, label=unit)
    
    ax4 = fig.add_subplot(224)
    goes_ts.plot(axes=ax4)
    ax4.axvline(highlight_time, color='steelblue', linewidth=1.5, label="t={}".format(highlight_time))
    ax4.legend()
    ax4.set_title("GOES X-Ray Flux")
    plt.tight_layout()
    plt.show()
