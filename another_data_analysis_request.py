# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 09:52:17 2021

@author: servanso from Deutschiftland/energiewende-entsoe-data
"""


import os # interaction with the operating system
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
        files = os.listdir('c:/Users/obenr/energiewende/data')
        timespan = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
        check_file = f"{timespan}_{country}_production.csv"
        if check_file in files:
            # file already exists, just read it
            dfc = pd.read_csv(f'c:/Users/obenr/energiewende/data/{check_file}', index_col=0)
        else:
            # request "Actual Generation per Production Type - Aggregated Generation per Type [16.1.B&C]" to API
            dfc = client.query_generation(country, start=start, end=end)
            if dfc.columns.nlevels == 2:
                # Suppression des valeurs de consommation (de toute manière vides)
                # Suppression du second niveau pour les noms de colonnes 
                # (la mention "Actual Aggregated" qui ne sert à rien)
                dfc = dfc.filter(regex='Actual Aggregated', axis=1).droplevel(1,axis=1)
            # write csv file to /data
            #dfc.rename(columns= {dfc.columns[0]:'date'}, inplace=True)
            dfc.to_csv(f"c:/Users/obenr/energiewende/data/{check_file}")
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

ctyColors={'DE':'xkcd:greenish brown','FR':'xkcd:sky blue','GB':'xkcd:bright green','IT':'xkcd:true blue',
           'ES':'xkcd:yellow','NL':'xkcd:tangerine','DK':'xkcd:light cyan','NO':'xkcd:fuchsia','CH':'xkcd:red',
           'PL':'xkcd:black','BE':'xkcd:baby pink','PT':'xkcd:brown','SE':'xkcd:neon purple'}

# user parameters
pwd_file = open( 'c:/data/txt/my ensoe token.txt','r')
TOKEN_API = pwd_file.read()
pwd_file.close()
client = EntsoePandasClient(api_key=TOKEN_API) #'${{ secrets.TOKEN_API }}')
year_start = 2015
year_end = 2022
country_code = ['DE','FR','GB','IT','ES','NL','DK','NO','CH','PL','BE','PT','SE']
color_codes = ['xkcd:greenish brown','xkcd:sky blue','xkcd:bright green','xkcd:true blue', 'xkcd:yellow','xkcd:tangerine','xkcd:light cyan',
               'xkcd:fuchsia','xkcd:red','xkcd:black','xkcd:baby pink','xkcd:brown','xkcd:neon purple']
timeStep = [1./4,1.,1./2,1.,1.,1./4,1.,1.,1.,1.,1.,1.,1.] # quarter hour data for germany,NL, half hour for GB hourly for others
unitConversion = [t/1000. for t in timeStep]
countryAverage =[]
for year in range(year_start, year_end):
    month_is_set = False
    #start = pd.Timestamp(year=year, month=1, day=1, tz='Europe/Brussels')
    #end = pd.Timestamp(year=year, month=12, day=31, tz='Europe/Brussels')
    # if we want monthly, add:
    start = pd.Timestamp(year=year, month=1, day=1, tz='Europe/Brussels')
    end = pd.Timestamp(year=year, month=12, day=start.daysinmonth, tz='Europe/Brussels')
    df, timespan = query_entsoe(start, end, country_code)
    emissionDf = [dfc.copy() for dfc in df]   
    for kcount,countr in enumerate(country_code):
        for source in df[kcount].keys():
            #print(df[kcount][[source]])
            emissionDf[kcount][source] = df[kcount][[source]].apply(multiply_by_sourceEm, args = (co2PerSource[source],unitConversion[kcount]))
    timespan = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
    [emissionDfc.to_csv(f"c:/data/csv/{timespan}_{country_code[index]}_emission.csv") for index, emissionDfc in enumerate(emissionDf)]
    totProd = [dfc.apply(np.nansum, axis=1) for dfc in df]
    totEmit = [emissionDfc.apply(np.nansum, axis=1) for emissionDfc in emissionDf]
    plt.axes(xlim=(0, 100000), ylim=(0, 800), autoscale_on=False)
    plt.title(str(year))
        # plot Cloud of points then average per country
    [plt.plot(totProd[k], totEmit[k]/totProd[k]/timeStep[k]*1000, '.',color=color_codes[k], markersize=2,alpha = 1./len(country_code)) for k in range(len(timeStep))]
    [plt.plot(sum(totProd[k])/len(totProd[k]),sum(totEmit[k])/sum(totProd[k])/timeStep[k]*1000,'.',color=color_codes[k],markersize = 8, alpha=1) for k in range(len(timeStep))]
    for k in range(len(country_code)):
        countryAverage.append(sum(totEmit[k])/sum(totProd[k])/timeStep[k]*1000)
    plt.gca().set_ylabel("Emissions (gCO2/kWh)")
    plt.gca().set_xlabel("Production (MWh)")
    plt.legend(country_code,fontsize = 'xx-small',labelcolor = color_codes,loc = 'upper right', markerscale = 3)
    filename = f"c:/data/png/{timespan}_{''.join(country_code)}_emission_vs_production.png"
    plt.savefig(filename, dpi=600, transparent = False)
    plt.clf()
    fig,axs = plt.subplots(4,3,sharex = True, sharey = True)
    fig.suptitle(str(year))
   
    for month in range(1,13):
        if year == 2021 and month> 3:
            break
        month_is_set = True
        start = pd.Timestamp(year=year, month=month, day=1, tz='Europe/Brussels')
        end = pd.Timestamp(year=year, month=month, day=start.daysinmonth, tz='Europe/Brussels')
        df, timespan = query_entsoe(start, end, country_code)
        emissionDf = [dfc.copy() for dfc in df]    
        totProd = [dfc.apply(np.nansum, axis=1) for dfc in df]
        totEmit = [emissionDfc.apply(np.nansum, axis=1) for emissionDfc in emissionDf]
        # convert from MW to co2 emission per country and source
        for kcount,countr in enumerate(country_code):
            for source in df[kcount].keys():
                #print(df[kcount][[source]])
                emissionDf[kcount][source] = df[kcount][[source]].apply(multiply_by_sourceEm, args = (co2PerSource[source],unitConversion[kcount]))
    
        # write csv file to /data with emissions per source in tons for each time step
        timespan = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
        [emissionDfc.to_csv(f"c:/data/csv/{timespan}_{country_code[index]}_emission.csv") for index, emissionDfc in enumerate(emissionDf)]
    
        # compute total production and emissions
        totProd = [dfc.apply(np.nansum, axis=1) for dfc in df]
        totEmit = [emissionDfc.apply(np.nansum, axis=1) for emissionDfc in emissionDf]
    
        # forces axes limit to overlay graphs
        #axs[int((month-1)/4)][(month-1)%3].axes(xlim=(0, 100000), ylim=(0, 800), autoscale_on=False)
    
        # plot
        [axs[int((month-1)/3)][(month-1)%3].plot(totProd[k], totEmit[k]/totProd[k]/timeStep[k]*1000, '.', markersize=2, color = color_codes[k],alpha = .4) for k in range(len(timeStep))]
        #axs[int((month-1)/4)][(month-1)%3].title(str(month))
        axs[int((month-1)/3)][(month-1)%3].xaxis.set_visible(False)
        axs[int((month-1)/3)][(month-1)%3].yaxis.set_visible(False)
        # save plot to .png
    for i in range(4):
        axs[i][0].yaxis.set_visible(True)
        axs[i][0].tick_params(axis='y', labelsize=4)
        if i%2 == 1:
            axs[i][0].set_ylabel("Emissions (gCO2/kWh)", fontsize = 'xx-small')
        #axs[i][0].set_xlabel("Production (MWh)",fontsize='xx-small')
    for i in range(3):
        axs[3][i].xaxis.set_visible(True)
        axs[3][i].tick_params(axis='x', labelsize=4)
        axs[3][i].set_xlabel("Production (MWh)",fontsize='xx-small')
        
    axs[3][2].legend(country_code, fontsize=2,markerscale=3)
    
    lines = []
    labels = []
    for ax in fig.axes:
        axLine, axLabel = ax.get_legend_handles_labels()
        lines.extend(axLine)
        labels.extend(axLabel)
    
        
    fig.legend(lines, labels,           
           loc = 'upper right',fontsize = 'xx-small')
    filename = f"c:/data/png/{timespan}_{''.join(country_code)}_monthly_emission_vs_production.png"
    fig.savefig(filename, dpi=600, transparent = False)

        # clear plot
    fig.clf()

for i in range(len(country_code)):
    c = []
    for k in range(7):
        c.append(countryAverage[i+k*len(country_code)])
    print(c)
    plt.plot(range(year_start,year_end),c,'-',color=color_codes[i])
plt.legend(country_code,loc='right',fontsize='xx-small')
plt.title('Average gCO2/KWh per year')
plt.gca().set_ylabel("Emissions (gCO2/kWh)")
plt.gca().set_xlabel("Year")  
filename = f"c:/data/png/{''.join(country_code)}_average_emission.png"
plt.savefig(filename, dpi=600, transparent = False)
plt.clf()
for i in range(len(country_code)):
    c = []
    for k in range(7):
        if country_code[i]=='IT':
            if k==0:
                c.append(100)
            else:
                c.append(100*countryAverage[i+k*len(country_code)]/countryAverage[i+len(country_code)])
        else:
            c.append(100*countryAverage[i+k*len(country_code)]/countryAverage[i])
    print(c)
    plt.plot(range(year_start,year_end),c,'-',color=color_codes[i])
plt.legend(country_code,loc='right',fontsize='xx-small')
plt.title('Evolution gCO2/KWh per year, 2015 = 100')
plt.gca().set_ylabel("Ratio")
plt.gca().set_xlabel("Year")  
filename = f"c:/data/png/{''.join(country_code)}_average_evolution.png"
#plt.show()
plt.savefig(filename, dpi=600, transparent = False)