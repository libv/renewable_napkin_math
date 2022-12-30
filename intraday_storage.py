#!/usr/bin/python

import csv

day = 0
intraday = []
storage_max = 0
storage_max_day = ''

with open('smard_consumption.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        new_day = row['Date']

        load = row['Total (grid load) [MWh]']
        if (load == '-'):
            break
        load = float(load)

        if (new_day == day):
            intraday.append(load)
            continue

        if (day):
            total = sum(intraday)
            average = total / 24

            storage = 0
            for value in intraday:
                # Compared to average, only one side is needed
                if (value > average):
                    storage += value - average

            losses = storage * .10
            storage /= 0.9
            if (storage_max < storage):
                storage_max = storage
                storage_max_day = day

            print("%s: %5.2fMW / %7.2fMWh : %06.2fMWh needed (%05.2fMWh loss)" % (day, average, total, storage, losses))

        day = new_day
        intraday = [load]

print("Maximum storage needed to flatten out intra-daily fluctuations: %06.2fMWh (%s)" % (storage_max, storage_max_day))
