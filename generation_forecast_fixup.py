#!/usr/bin/python

#
# SMARD generation forecast data has holes, patch the holes with
# actual generation data.
#

import sys
import csv

if (len(sys.argv) != 4):
    print("Error: Wrong number of arguments.")
    print("%s <forecast input csv> <actual input csv> <output csv>" % (sys.argv[0]))
    sys.exit()

filename_forecast_input = sys.argv[1]
filename_actual_input = sys.argv[2]
filename_output = sys.argv[3]

output = [ ]

print("Reading forecast generation data from %s" % filename_forecast_input)
print("Reading actual generation data from %s" % filename_actual_input)

file_forecast = open(filename_forecast_input, mode='r')
reader_forecast = csv.DictReader(file_forecast)
fieldnames_forecast = reader_forecast.fieldnames

#print(fieldnames_forecast)

file_actual = open(filename_actual_input, mode='r')
reader_actual = csv.DictReader(file_actual)

#print(reader_actual.fieldnames)

while True:
    forecast = next(reader_forecast, None)
    if (forecast == None):
        break
    #print(forecast)

    actual = next(reader_actual, None)
    if (actual == None):
        break
    #print(actual)

    if ((forecast['Date'] != actual['Date']) or
        (forecast['Start'] != actual['Start'])):
        print("Error: mismatched rows:")
        print("  forecast: %s %s" % (forecast['Date'], forecast['Start']))
        print("  actual: %s %s" % (actual['Date'], actual['Start']))
        sys.exit()

    if (forecast['Wind offshore [MWh]'] == '-'):
        print("Fixing up offshore wind for %s %s" % (forecast['Date'], forecast['Start']))
        forecast['Wind offshore [MWh]'] = actual['Wind offshore [MWh]']

    if (forecast['Wind onshore [MWh]'] == '-'):
        print("Fixing up onshore wind for %s %s" % (forecast['Date'], forecast['Start']))
        forecast['Wind onshore [MWh]'] = actual['Wind onshore [MWh]']

    if (forecast['Photovoltaics [MWh]'] == '-'):
        print("Fixing up Photovoltaics wind for %s %s" % (forecast['Date'], forecast['Start']))
        forecast['Photovoltaics [MWh]'] = actual['Photovoltaics [MWh]']

    output.append(forecast)

print("Writing fixed generation forecast data to %s" % filename_output)

with open(filename_output, mode='w') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames_forecast,
                                lineterminator='\n')

    csv_writer.writeheader()
    csv_writer.writerows(output)
