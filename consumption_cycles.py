#!/usr/bin/python

#
# This program calculates the average "daily" cycleconsumption and the area
# above the average of a 24h cycle starting at 22:00 the previous day.
# This cycle area is a measure for how much grid level storage is needed
# to flatten intra-day fluctuations in the electricity grid.
#

import sys
import csv

if (len(sys.argv) != 3):
    print("Error: Wrong number of arguments.")
    print("%s <input csv> <output csv>" % (sys.argv[0]))
    sys.exit()

filename_input = sys.argv[1]
filename_output = sys.argv[2]

intraday = []
cycles = [ ]

storage_max = 0
storage_max_day = ""

yearly_daily = 0.0
yearly_storage = 0.0
yearly_days = 0

print("Reading data from %s" % filename_input)

with open(filename_input, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        date = row['Date']
        time = row['Time']
        load = row['Total (grid load) [MWh]']

        # could be bad data or end of data
        if (load == '-'):
            break

        load = float(load)

        if (time != "22:00"):
            intraday.append(load)
            continue

        total = sum(intraday)
        if (date == "2015-01-01"):
            average = total / 22
        else:
            average = total / 24

        storage = 0
        for value in intraday:
            # Compared to average, only one side is needed
            # take the curve above as the first day cycle misses 2h
            if (value > average):
                storage += value - average
        intraday = [load]

        cycle = { 'Date' : date,
                  'Total Consumption [MWh]' : total,
                  'Average Consumption [MW]' : round(average, 2),
                  'Storage Cycle [MWh]' : round(storage,2) }
        cycles.append(cycle)

        if (storage_max < storage):
            storage_max = storage
            storage_max_day = date

        print("%s: %5.2fMW / %7.2fMWh : %06.2fMWh needed" %
              (date, average, total, storage))

        yearly_days += 1
        yearly_daily += total
        yearly_storage += storage

        if (date.endswith("-12-31")):
            yearly_daily /= yearly_days
            yearly_storage /= yearly_days
            print("%s average (%ddays): %5.2fMW / %7.2fMWh :  %06.2fMWh needed"
                  % (date[0:4], yearly_days, yearly_daily / 24, yearly_daily,
                     yearly_storage))
            yearly_daily = 0.0
            yearly_storage = 0.0
            yearly_days = 0

print("Maximum intra-day storage needed: %6.2fMWh (%s)" %
      (storage_max, storage_max_day))

print("Writing data to %s" % filename_output)

with open(filename_output, mode='w') as csv_file:
    fieldnames = ['Date', 'Total Consumption [MWh]',
                  'Average Consumption [MW]', 'Storage Cycle [MWh]']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    csv_writer.writeheader()
    csv_writer.writerows(cycles)
