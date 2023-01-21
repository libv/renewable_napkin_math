#!/usr/bin/python

#
# Unify SMARD consumption and generation data, for wind and solar,
# so it can be used to project consumption vs generation with theoretically
# installed capacities.
#
# Installed capacity is not granular below a year, so we interpolate daily.
#
# We keep the generation information as a fraction of installed capacity for
# ease of calculation.
#
#
# Data for new capacity for 2022 is still preliminary: 7200.0 of solar,
# 2000.0 for onshore wind. Offshore wind is already known at a total of 8129MW

import sys
import csv

if (len(sys.argv) != 7):
    print("Error: Wrong number of arguments.")
    print("%s <consumption forecast csv> <consumption actual csv> <generation "
          "forecast csv> <generation actual csv> <generation capacity csv> <output csv>" % (sys.argv[0]))
    sys.exit()

load_forecast_filename = sys.argv[1]
load_actual_filename = sys.argv[2]
capacity_filename = sys.argv[3]
forecast_filename = sys.argv[4]
actual_filename = sys.argv[5]
result_filename = sys.argv[6]

#print("Reading grid load forecast data from %s" % load_forecast_filename)
#print("Reading actual grid load data from %s" % load_actual_filename)
#print("Reading generation capacity data from %s" % capacity_filename)
#print("Reading generation forecast data from %s" % forecast_filename)
#print("Reading actual generation data from %s" % actual_filename)
#print("Writing resulting generation data to %s" % result_filename)

year_start = 10000
year_end = 0

#
# SMARD installed capacity data is not granular. It mostly gets updated
# once a year. So first create dict with yearly capacity numbers, then
# calculate the linear interpolation per day.
#

capacity_yearly = {}
with open(capacity_filename, mode='r') as capacity_file:
    capacity_reader = csv.DictReader(capacity_file)
    for row in capacity_reader:
        if (row['Date'].endswith("-01-01") and
            row['Time'] == "00:00"):
            year = int(row['Date'][0:4])
            if (year < year_start):
                year_start = year
            if (year > year_end):
                year_end = year
            capacity = {'Year' : year,
                        'Photovoltaics' : float(row['Photovoltaics [MW]']),
                        'Wind onshore' : float(row['Wind onshore [MW]']),
                        'Wind offshore' : float(row['Wind offshore [MW]'])}
            capacity_yearly[year] = (capacity)

year_end = 2023

capacity_interpolated = {}

for year in range(year_start, year_end):
    current = capacity_yearly[year]
    future = capacity_yearly[year + 1]

    if ((year % 4) == 0):
        days = 366
    else:
        days = 365

    current['Photovoltaics growth'] = (future['Photovoltaics'] - current['Photovoltaics']) / days
    current['Wind onshore growth'] = (future['Wind onshore'] - current['Wind onshore']) / days
    current['Wind offshore growth'] = (future['Wind offshore'] - current['Wind offshore']) / days

    #print(current)
    capacity_interpolated[year] = current


#
# Now run through the data, and calculated the percentage
#
load_forecast_file = open(load_forecast_filename, mode='r')
load_forecast_reader = csv.DictReader(load_forecast_file)

load_actual_file = open(load_actual_filename, mode='r')
load_actual_reader = csv.DictReader(load_actual_file)

forecast_file = open(forecast_filename, mode='r')
forecast_reader = csv.DictReader(forecast_file)

actual_file = open(actual_filename, mode='r')
actual_reader = csv.DictReader(actual_file)

result_file = open(result_filename, mode='w')
result_fieldnames = ['Date',
                     'Time',
                     'Load forecast',
                     'Load actual',
                     'Hydropower actual',
                     'Wind onshore forecast',
                     'Wind onshore actual',
                     #'Wind onshore capacity',
                     'Wind offshore forecast',
                     'Wind offshore actual',
                     #'Wind offshore capacity',
                     'Photovoltaics forecast',
                     'Photovoltaics actual',
                     #'Photovoltaics capacity',
]
result_writer = csv.DictWriter(result_file, fieldnames=result_fieldnames,
                               lineterminator='\n')
result_writer.writeheader()

photovoltaics_capacity = 0.0
wind_onshore_capacity = 0.0
wind_offshore_capacity = 0.0
photovoltaics_growth = 0.0
wind_onshore_growth = 0.0
wind_offshore_growth = 0.0

while True:
    load_forecast = next(load_forecast_reader, None)
    if (load_forecast == None):
        break
    #print(load_forecast)

    load_actual = next(load_actual_reader, None)
    if (load_actual == None):
        break
    #print(load_actual)

    forecast = next(forecast_reader, None)
    if (forecast == None):
        break
    #print(forecast)

    actual = next(actual_reader, None)
    if (actual == None):
        break
    #print(actual)

    if ((load_forecast['Date'] != load_actual['Date']) or
        (load_forecast['Start'] != load_actual['Time']) or
        (load_forecast['Date'] != actual['Date']) or
        (load_forecast['Start'] != actual['Start']) or
        (forecast['Date'] != actual['Date']) or
        (forecast['Start'] != actual['Start'])):
        print("Error: mismatched rows:")
        print("  load_forecast: %s %s" % (load_forecast['Date'], load_forecast['Start']))
        print("  load_actual: %s %s" % (load_actual['Date'], load_actual['Time']))
        print("  forecast: %s %s" % (forecast['Date'], forecast['Start']))
        print("  actual: %s %s" % (actual['Date'], actual['Start']))
        sys.exit()

    if (forecast['Start'] == "00:00"):
        if (forecast['Date'].endswith("-01-01")):
            year = int(forecast['Date'][0:4])
            capacity = capacity_interpolated[year]
            photovoltaics_capacity = capacity['Photovoltaics']
            wind_onshore_capacity = capacity['Wind onshore']
            wind_offshore_capacity = capacity['Wind offshore']
            photovoltaics_growth = capacity['Photovoltaics growth']
            wind_onshore_growth = capacity['Wind onshore growth']
            wind_offshore_growth = capacity['Wind offshore growth']

            #print("%d: Photovoltaics %f + %f, Wind onshore %f + %f, Wind offshore %f + %f" %
            #      (year, photovoltaics_capacity, photovoltaics_growth, wind_onshore_capacity,
            #       wind_onshore_growth, wind_offshore_capacity, wind_offshore_growth))
        else:
            photovoltaics_capacity += photovoltaics_growth
            wind_onshore_capacity += wind_onshore_growth
            wind_offshore_capacity += wind_offshore_growth

    result = {'Date': forecast['Date'],
              'Time': forecast['Start'],
              'Load forecast' : round(float(load_forecast['Total (grid load) [MWh]']), 2),
              'Load actual' : round(float(load_actual['Total (grid load) [MWh]']), 2),
              'Hydropower actual' : actual['Hydropower [MWh]'],
              'Photovoltaics forecast': round((float(forecast['Photovoltaics [MWh]']) / photovoltaics_capacity), 4),
              'Photovoltaics actual': round((float(actual['Photovoltaics [MWh]']) / photovoltaics_capacity), 4),
              #'Photovoltaics capacity': round(photovoltaics_capacity, 2),
              'Wind onshore forecast': round((float(forecast['Wind onshore [MWh]']) / wind_onshore_capacity), 4),
              'Wind onshore actual': round((float(actual['Wind onshore [MWh]']) / wind_onshore_capacity), 4),
              #'Wind onshore capacity': round(wind_onshore_capacity, 2),
              'Wind offshore forecast': round((float(forecast['Wind offshore [MWh]']) / wind_offshore_capacity), 4),
              'Wind offshore actual': round((float(actual['Wind offshore [MWh]']) / wind_offshore_capacity), 4),
              #'Wind offshore capacity': round(wind_offshore_capacity, 2),
    }

    #print(result)
    result_writer.writerow(result)
