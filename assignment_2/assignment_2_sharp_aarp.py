import sunpy.map as map
from sunpy.net import Fido, attrs as a
import matplotlib, matplotlib.pyplot as plt
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np
from sunkit_instruments import goes_xrs
from sunpy.time import TimeRange
import pandas as pd
import sunpy.visualization.colormaps as cm
from assignment_1_goes_time_series import get_start_and_end_time, fetch_goes_data, get_time_and_window

    
def fetch_flare_events(start_time, end_time):
    flare_events = goes_xrs.get_goes_event_list(TimeRange(start_time, end_time))
    flare_df = pd.DataFrame(flare_events)
    return flare_df

def check_if_ar_flared(flare_df, noaa_numbers, timestamp):
    
    # Check if flare dataframe is empty which means no flare events were detected.
    if flare_df.empty:
        return False
    
    if noaa_numbers.size == 0:
        print("NOAA numbers are missing cannot check if flare occured.")
    
    for noaa in noaa_numbers:
        # Filter the dataframe to get flare events for the specific NOAA number
        flares_for_noaa = flare_df[flare_df['noaa_active_region'] == noaa]
        # Iterate over the filtered DataFrame
        for _, flare in flares_for_noaa.iterrows():
            start_time = flare['start_time']
            end_time = flare['end_time']
            # Check if the timestamp is within the start and end time of the flare
            if start_time <= timestamp <= end_time:
                return True
    return False


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
    
    # Obtain NOAA number to check if active region has flared
    noaa_numbers = sharp_result[0]["NOAA_ARS"]
    noaa_string = noaa_numbers[0].item()
    
    if noaa_string != 'MISSING':
       noaa_num_array = np.array(noaa_string.split(','), dtype='int')
    else:
       noaa_num_array = np.array([]) 

    files = Fido.fetch(sharp_result)
    sharp_maps = map.Map(files)
    return sharp_maps, noaa_num_array


def fix_metadata(sharp_maps):
    """
    Fix metadata issues for SHARP maps. ###WIP###
    """
    if isinstance(sharp_maps, list):
        for smap in sharp_maps:
            if "bunit" in smap.meta and smap.meta["bunit"] == "Mx/cm^2":
                smap.meta["bunit"] = r"Mx cm$^{-2}$"
    else:
        if "bunit" in sharp_maps.meta and sharp_maps.meta["bunit"] == "Mx/cm^2":
            sharp_maps.meta["bunit"] = r"Mx cm$^{-2}$"
    return sharp_maps

def plot_combined_data(sharp_map, aarp_filepaths, goes_ts, start_time, end_time, highlight_time, flared):
    fig = plt.figure(figsize=(15, 10))
    
    # Plot SHARP data with its WCS projection
    ax1 = fig.add_subplot(221, projection=sharp_map)
    im1 = ax1.imshow(sharp_map.data, cmap='afmhot', origin='lower')
    harpnum = sharp_map.meta.get('HARPNUM')
    sharp_time = sharp_map.date
    sharp_unit = sharp_map.meta.get('bunit', 'Unknown')
    sharp_x_unit = sharp_map.meta.get('cunit1', 'degree')
    sharp_y_unit = sharp_map.meta.get('cunit2', 'degree')
    ax1.set_title(f"SHARP - {harpnum} at {sharp_time} | AR flared - {flared}")
    ax1.set_xlabel(f"CEA Longitude ({sharp_x_unit})")
    ax1.set_ylabel(f"CEA Latitude ({sharp_y_unit})")
    plt.colorbar(im1, ax=ax1, label=sharp_unit)
    
    # Plot AARP data with adjusted vmin and vmax
    for i, filepath in enumerate(aarp_filepaths):
        with fits.open(filepath) as hdul:
            ext = hdul[1]
            time_key = f"T_IMG05"
            specific_time = ext.header.get(time_key, 'Unknown')
            aarp_wavelength = ext.header.get('WAVELNTH', 'Unknown')
            aarp_colormap = matplotlib.colormaps[f'sdoaia{aarp_wavelength}']
            data = ext.data[5, :, :]

            # Extract WCS information from the header
            wcs = WCS(ext.header, naxis=2)
            ax = fig.add_subplot(2, 2, i+2, projection=wcs)
            
            # Calculate vmin and vmax for better dynamic range
            vmin = np.percentile(data, 1)
            vmax = np.percentile(data, 99.5)

            im = ax.imshow(data, cmap=aarp_colormap, origin='lower', aspect='auto', vmin=vmin, vmax=vmax)
            aarp_x_unit = ext.header.get('CUNIT1', 'Unknown')
            aarp_y_unit = ext.header.get('CUNIT2', 'Unknown')
            unit = ext.header.get('BUNIT', 'Intensity')  # Get unit for colorbar from header if available
            ax.coords[0].set_axislabel(f'Solar X ({aarp_x_unit})')
            ax.coords[1].set_axislabel(f'Solar Y ({aarp_y_unit})')
            ax.set_title(f'AARP - {aarp_wavelength} Å at {specific_time}')
            plt.colorbar(im, ax=ax, label=unit)
    
    # Plot GOES data in the 2x2 grid
    ax4 = fig.add_subplot(224)
    goes_ts.plot(axes=ax4)
    ax4.axvline(highlight_time, color='steelblue', linewidth=1.5, label="t={}".format(highlight_time))
    ax4.legend()
    ax4.set_title("GOES X-Ray Flux")
    plt.tight_layout()
    plt.show()



def main():
    timestamp, time_window_minutes = get_time_and_window()
    start_time, end_time = get_start_and_end_time(timestamp, time_window_minutes)
    flare_df = fetch_flare_events(start_time, end_time)
    available_harpnums = fetch_harpnums(timestamp)
    harpnum = select_harpnum(available_harpnums)

    try:
        print(f"Fetching SHARP data for {timestamp}...")
        sharp_maps, noaa_numbers = fetch_sharp_data(timestamp, harpnum)
        ar_flared = check_if_ar_flared(flare_df, noaa_numbers, timestamp)
        sharp_maps = fix_metadata(sharp_maps)
        print("SHARP data fetched successfully. Plotting the data...")

        print(f"Fetching GOES data from {start_time} to {end_time}...")
        goes_ts = fetch_goes_data(start_time, end_time)
        print("GOES data fetched successfully. Plotting the data...")

        aarp_filepaths = [
            r"C:\Users\vaina\OneDrive\Documents\Kerala Internship\assignment_2\AARP fits files\2011.05.28_15 48 00_7h@1h_AARP625_171.fits",
            r"C:\Users\vaina\OneDrive\Documents\Kerala Internship\assignment_2\AARP fits files\2011.05.28_15 48 00_7h@1h_AARP625_304.fits"
        ]

        plot_combined_data(sharp_maps, aarp_filepaths, goes_ts, start_time, end_time, timestamp, ar_flared)
        print("Plot displayed successfully.")
    except RuntimeError as fetch_error:
        print(fetch_error)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
