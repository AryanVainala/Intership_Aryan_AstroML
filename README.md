# Assignment 2: Integration and Visualization of SHARP, AARP, and GOES Data for Solar Analysis

## Description

This project involves the integration and visualisation of data from three different solar observation sources: SHARP (Solar Active Region Patches), AARP (Active Region Patches), and GOES (Geostationary Operational Environmental Satellite). The code fetches data based on a specified timestamp which can return multiple HARPNUM (HMI Active Region Patch Number) regions and time window, processes the data to fix any metadata issues, and then displays the data in a combined plot to allow for comprehensive solar analysis.

The steps involved in the code are as follows:
```mermaid
flowchart TD
A([Start])-->B[Get time stamp and time window]-->C[Fetch available HARPNUM for SHARP data]-->D[Select HARPNUM]-->E[Fetch data for timestamp and HARPNUM from JSOC]-->F[Fetch GOES data]-->G[Fix SHARP metadata]-->H[Load AARP .fits files]-->I[Check if Active Region Flared]-->J[Plot SHARP, AARP images and GOES timeseries]
```


