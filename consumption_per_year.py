#!/usr/bin/python

import sys
import csv

if (len(sys.argv) != 2):
    print("Error: Wrong number of arguments.")
    print("%s <consumption data csv> " % (sys.argv[0]))
    sys.exit()

consumption_filename = sys.argv[1]

year = 0
consumption = 0.0

with open(consumption_filename, mode='r') as consumption_file:
    consumption_reader = csv.DictReader(consumption_file)
    for row in consumption_reader:
        if (row['Date'].endswith("-01-01") and
            row['Time'] == "00:00"):
            year = int(row['Date'][0:4])
            consumption = float(row['Total (grid load) [MWh]'])
        elif (row['Date'].endswith("-12-31") and
            row['Time'] == "23:00"):
            consumption += float(row['Total (grid load) [MWh]'])
            print("%d: %7.3fTWh" % (year, consumption / 1000000.0))
        else:
            consumption += float(row['Total (grid load) [MWh]'])
