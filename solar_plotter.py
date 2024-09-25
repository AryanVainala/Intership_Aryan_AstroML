from solar_library import (fetch_goes_data, fetch_sharp_data, plot_combined_data, plot_animation,get_time_and_window,
                            get_start_and_end_time, fix_metadata, plot_time_series, 
                            fetch_flare_events, check_if_ar_flared)

class SolarPlotter:
    def __init__(self, sharp=False, aarp=False):
        self.sharp = sharp
        self.aarp = aarp

    def plot_data(self):
        timestamp, time_window_minutes = get_time_and_window()
        start_time, end_time = get_start_and_end_time(timestamp, time_window_minutes)

        goes_ts = fetch_goes_data(start_time, end_time)
        
        if self.sharp:
            sharp_maps, noaa_numbers = fetch_sharp_data(timestamp, timestamp)
            sharp_maps = fix_metadata(sharp_maps)
            
            flare_df = fetch_flare_events(start_time, end_time)
            ar_flared = check_if_ar_flared(flare_df, noaa_numbers, timestamp)
        
        if self.aarp:
            aarp_filepaths = [
                r"C:\Users\vaina\OneDrive\Documents\Kerala Internship\aarp_fits_files\2011.05.28_15 48 00_7h@1h_AARP625_171.fits",
                r"C:\Users\vaina\OneDrive\Documents\Kerala Internship\aarp_fits_files\2011.05.28_15 48 00_7h@1h_AARP625_304.fits"
            ]

        if self.sharp and self.aarp:
            plot_combined_data(sharp_maps, aarp_filepaths, goes_ts, timestamp, ar_flared)
        elif self.sharp:
            plot_combined_data(sharp_maps, [], goes_ts, timestamp, ar_flared)
        else:
            plot_time_series(goes_ts, timestamp)
        
    def plot_animation(self):
        timestamp, time_window_minutes = get_time_and_window()
        start_time, end_time = get_start_and_end_time(timestamp, time_window_minutes)
        sharp_maps, noaa_numbers = fetch_sharp_data(start_time, end_time)
        sharp_maps = fix_metadata(sharp_maps)
        plot_animation(sharp_maps)