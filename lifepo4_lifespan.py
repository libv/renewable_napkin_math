#!/usr/bin/python

#
# This program takes a daily consumption csv and cycles a GWh grid scale
# battery to flatten the grid load curve.
#
# It calculates the loss of capacity through charge/discharge cycles.
#
# Finally, it produces a cost analysis based on some 3 existing batteries.
#

import sys
import csv
from decimal import Decimal

verbose = False

if (len(sys.argv) != 4):
    print("Error: Wrong number of arguments.")
    print("%s <daily consumption csv> <capacity GWh> <life years>" % (sys.argv[0]))
    sys.exit()

consumption_filename = sys.argv[1]
capacity_original = float(sys.argv[2]) * 1000.0
duration = int(sys.argv[3])

capacity = capacity_original
volume_total = 0.0
days = 0
days_short = 0
years = 0

#
# https://www.powertechsystems.eu/home/tech-corner/lithium-iron-phosphate-lifepo4/
# has a chart which estimates the number of cycles a lifepo4 battery has compared
# to depth of discharge.
#
# We assume that .25C is a good enough charge/discharge rate for 10s of GWh scale grid level storage.
#
# The values were manually guesstimated from the chart.
#
dod_cycles = {100:    6000.0,
               95:    6700.0,
               90:    7000.0,
               85:    8000.0,
               80:    8900.0,
               75:   10000.0,
               70:   13000.0,
               65:   16000.0,
               60:   19000.0,
               55:   24000.0,
               50:   31000.0,
               45:   40000.0,
               40:   52000.0,
               35:   73000.0,
               30:  100000.0,
               25:  160000.0,
               20:  240000.0,
               15:  370000.0,
               10:  650000.0,
                5: 1000000.0} # guess, no more data

#
# After 6000.0 100% cycles the battery will have degraded to 80% original capacity.
#
# So 20 divided by each value is a very rough estimate for the percentage that
# a lifepo4 battery degrades for each depth of discharge.
#
for dod in dict.keys(dod_cycles):
    if (verbose == True):
        print("%3s%% DoD: %f%% capacity loss" % (dod, 20.0 / float(dod_cycles[dod])))
    dod_cycles[dod] = 20.0 / float(dod_cycles[dod])

def cycle(date, cycle_volume):
    global capacity
    global volume_total
    global days_short

    # Battery round-trip is 90% efficient, mostly inverter losses.
    # But this is round-trip, so when charging it is 5%.
    # When discharging, 5% of actual battery capacity is lost again.
    cycle_percentage = 100.0 * cycle_volume / (capacity * 0.95)

    dod = 5 * int(cycle_percentage / 5)
    if (dod < cycle_percentage):
        dod += 5

    missing = 0.0
    if (dod > 100.0):
        missing = cycle_volume - (capacity * 0.95)
        days_short += 1
        dod = 100.0

    volume_total += cycle_volume - missing

    reduction = dod_cycles[dod]
    capacity -= reduction * capacity_original / 100.0

    if (verbose == False):
        return

    if (cycle_percentage > 100.0):
        print("%s: %9.2fMWh: %6.2f%% cycle : %4.2fGWh capacity remaining (%2.2fMWh short)" %
              (date, cycle_volume, cycle_percentage, capacity / 1000.0, missing))
    else:
        print("%s: %9.2fMWh: %6.2f%% cycle : %4.2fGWh capacity remaining" %
              (date, cycle_volume, cycle_percentage, capacity / 1000.0))

while True:
    with open(consumption_filename, mode='r') as consumption_file:
        consumption_reader = csv.DictReader(consumption_file)
        for consumption in consumption_reader:
            date = consumption['Date']
            cycle(date, float(consumption['Storage Cycle [MWh]']))

            days += 1
            if (date.endswith("-12-31")):
                years += 1
                if (years >= duration):
                    break
    if (years >= duration):
        break

print("After %d years (%d days), %4.2fGWh of grid scale battery storage has %4.2fGWh (%2.2f%%) capacity remaining." %
      ((days / 365), days, capacity_original / 1000.0, capacity / 1000.0,
       100.0 * capacity / capacity_original))
print("A total of %9.2fGWh was cycled through the battery." % (volume_total / 1000.0))
print("Cycle efficiency losses amount to %9.2fGWh (10%%), the average required generation capacity increase is %6.2fMW." %
      (volume_total / 10000.0, volume_total / days / 240.0))

if (days_short):
    print("%4.2fGWh of grid level battery storage was not able to fully cover intra-day variations on %d days." %
          (capacity_original / 1000.0, days_short))
