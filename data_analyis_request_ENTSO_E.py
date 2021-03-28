#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from entsoe import EntsoePandasClient

def multiply_by_sourceEm(arr,sourceEm,unitConv):
    """
    converts power to co2 emission

    Parameters
    ----------
    arr : array
        electricity power per time step for 1 country and 1 source (MW)
    sourceEm : float
        co2 intensity for 1 source in Kgco2eq/MWh
    unitConv : float
        conversion rate from MW to MWh (x time step) and from kgco2 to tco2 (/1000)
        warning: time step not the same for all countries, 
        we use timeStep parameter to define number of time steps per hour (manual entry)

    Returns
    -------
    array
        co2 emission per time step

    """
    return np.multiply(arr,sourceEm*unitConv)

def query_entsoe(start, end, country_list):
    """
    queries ENTSOE database if data not already available

    Parameters
    ----------
    start : timestamp
        start of the period queried (day)
    end : timestamp
        end of the period queried (day)
    country_list : list
        list of countries to retrieve

    Returns
    -------
    df : TYPE
        DESCRIPTION.
    timespan : TYPE
        DESCRIPTION.

    """
    df = []
    for country in country_list:
        # check if file already exists
        files = os.listdir('./data')
        timespan = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
        check_file = f"{timespan}_{country}_production.csv"
        if check_file in files:
            # file already exists, just read it
            dfc = pd.read_csv(f'./data/{check_file}', index_col=0)
        else:
            # request "Actual Generation per Production Type - Aggregated Generation per Type [16.1.B&C]" to API
            dfc = client.query_generation(country, start=start, end=end)
            if dfc.columns.nlevels == 2:
                # Suppression des valeurs de consommation (de toute manière vides)
                # Suppression du second niveau pour les noms de colonnes 
                # (la mention "Actual Aggregated" qui ne sert à rien)
                dfc = dfc.filter(regex='Actual Aggregated', axis=1).droplevel(1,axis=1)
            # write csv file to /data
            dfc.rename(columns= {df.columns[0]:'date'}, inplace=True)
            dfc.to_csv(f"./data/{check_file}")
        # reconstitute df for country_list
        df.append(dfc)
    return df, timespan

# CO2 emission of each technology in a dictionary
# unite: gco2eq/kWh = Kg co2eq/MWh
# source: https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf
# by default we refer to emission numbers in the table A.III.2 (median of life cycle analyses), 
# otherwise we indicate the source with the numbers
# used the biomass "dedicated", must check what is the dominant tech in each country...
# used generic "coal" emission for both brown and hard coal,
# all hydros use same number (24)

co2PerSource = {
    'Biomass': 230.,
    'Fossil Brown coal/Lignite': 820.,
    'Fossil Coal-derived gas': 490., # could not find numbers for coal derived gas, use fossil gas but probably very wrong!
    'Fossil Gas': 490.,
    'Fossil Hard coal': 820.,
    'Fossil Oil': 733., # mean value of table 2 in https://www.world-nuclear.org/uploadedFiles/org/WNA/Publications/Working_Group_Reports/comparison_of_lifecycle.pdf
    'Fossil Oil shale': 733.,
    'Fossil Peat': 820., # could not find numbers for peat, use coal value
    'Geothermal': 38.,
    'Hydro Pumped Storage': 24.,
    'Hydro Run-of-river and poundage': 24.,
    'Hydro Water Reservoir': 24.,
    'Marine': 17., # used 'ocean' in 'pre-commercial technologies' for marine, not sure!
    'Nuclear': 12.,
    'Other': 820., # used coal for other (conservative), to be refined!
    'Other renewable': np.nan,
    'Solar': 41., # used PV for solar
    'Waste': 922.22, # for waste, note sure but used the first row of table 1 in https://www.mdpi.com/2071-1050/8/11/1181
    'Wind Offshore': 12.,
    'Wind Onshore': 11.
    }

# user parameters
client = EntsoePandasClient(api_key='${{ secrets.TOKEN_API }}')
year_start = 2015
year_end = 2021
country_code = ['DE','FR']
timeStep = [1./4.,1.] # quarter hour data for germany, hourly for france
unitConversion = [t/1000. for t in timeStep]

for year in range(year_start, year_end):
    start = pd.Timestamp(year=year, month=1, day=1, tz='Europe/Brussels')
    end = pd.Timestamp(year=year, month=12, day=31, tz='Europe/Brussels')
    # if we want monthly, add:
    #for month in range(1,13):
        #start = pd.Timestamp(year=year, month=month, day=1, tz='Europe/Brussels')
        #end = pd.Timestamp(year=year, month=month, day=start.daysinmonth, tz='Europe/Brussels')
    
    # call query
    df, timespan = query_entsoe(start, end, country_code)
    emissionDf = [dfc.copy() for dfc in df]    

    # convert from MW to co2 emission per country and source
    for kcount,countr in enumerate(country_code):
        for source in df[kcount].keys():
            emissionDf[kcount][source] = df[kcount][[source]].apply(multiply_by_sourceEm, args = (co2PerSource[source],unitConversion[kcount]))

    # write csv file to /data with emissions per source in tons for each time step
    timespan = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
    [emissionDfc.to_csv(f"./data/{timespan}_{country_code[index]}_emission.csv") for index, emissionDfc in enumerate(emissionDf)]

    # compute total production and emissions
    totProd = [dfc.apply(np.nansum, axis=1) for dfc in df]
    totEmit = [emissionDfc.apply(np.nansum, axis=1) for emissionDfc in emissionDf]

    # forces axes limit to overlay graphs
    plt.axes(xlim=(0, 100000), ylim=(0, 800), autoscale_on=False)

    # plot
    [plt.plot(totProd[k], totEmit[k]/totProd[k]/timeStep[k]*1000, '.', markersize=2) for k in range(len(timeStep))]
    plt.gca().set_ylabel("Emissions (gCO2/kWh)")
    plt.gca().set_xlabel("Production (MWh)")
    plt.legend(country_code)

    # save plot to .png
    filename = f"./plots/{timespan}_{''.join(country_code)}_emission_vs_production.png"
    plt.savefig(filename, dpi=300, transparent = True)

    # clear plot
    plt.clf()
