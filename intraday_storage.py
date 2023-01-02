#!/usr/bin/python

import csv

day = 0
intraday = []

storage_max = 0
storage_max_day = ''
storage_max_hours = 0

# Germany officially has 37700MWh of storage, and that can be drained at
# 6565MW, or a C factor of 0.17. (1/5.7)
# Not all of that is active today, so take 30000MWh
storage_pumped = 30000
storage_pumped_efficiency = 0.75

storage_battery = 0.0
storage_battery_efficiency = 0.90

# Status 20221230: https://www.tesla.com/megapack/design
# 1000 4h Megapacks are 3916 MWh (969.6 MW) installed and delivered
# to california in Q3 2024. This equates to 468usd per kW, or 437EUR
battery_cost_megapack = 437000

# Status 20221230: https://trophybattery.com/index.php/model-48v220e-1-2/
# 4695usd / 15.360kW = 306usd/kW or 286EUR
battery_cost_serverrack = 286000

# Status 20221230: https://qiso.en.alibaba.com/
# Eve LF-280K, 5000+ pieces, delivered with customs to germany: 93.80EUR
battery_cost_raw_cells = 104687

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

            storage_hours = storage / average

            if (storage_max < storage):
                storage_max = storage
                storage_max_day = day
                storage_max_hours = storage_hours

            print("%s: %5.2fMW / %7.2fMWh : %06.2fMWh needed (%1.2fh)" %
                  (day, average, total, storage, storage_hours))

        day = new_day
        intraday = [load]

print("")
print("Maximum intra-day storage needed:  %6.2fMWh (%s, %1.2fh)" % (storage_max, storage_max_day, storage_max_hours))

print("  Pumped Hydro Storage available: %6.2fMWh (%6.2fMWh@%.2f%% efficiency)" % (storage_pumped * storage_pumped_efficiency, storage_pumped, storage_pumped_efficiency))

storage_battery = storage_max - (storage_pumped * storage_pumped_efficiency)
storage_battery /= storage_battery_efficiency

print("  Battery storage needed:  %6.2fMWh (%6.2fMWh@%.2f%% efficiency)" % (storage_battery * storage_battery_efficiency, storage_battery, storage_battery_efficiency))

print("")
print("Cost Breakdown:")
print("  In Tesla Megapacks (Q4 2022): %3.3fB EUR" % (storage_battery * battery_cost_megapack / 1000000000.0))
print("  As Serverrack batteries (Trophy, Q4 2022): %3.3fB EUR" % (storage_battery * battery_cost_serverrack / 1000000000.0))
print("  As Raw cells (Eve LF280k, Qiso, Q4 2022): %3.3fB EUR" % (storage_battery * battery_cost_raw_cells / 1000000000.0))
