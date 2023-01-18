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

if (len(sys.argv) != 8):
    print("Error: Wrong number of arguments.")
    print("%s <generation data csv> <load factor> <onshore wind GW> <offshore wind GW> <solar GW> <storage GWh> <biogas GW> " %
          (sys.argv[0]))
    sys.exit()

data_filename = sys.argv[1]
load_factor = float(sys.argv[2])
capacity_onshore = float(sys.argv[3]) * 1000.0
capacity_offshore = float(sys.argv[4]) * 1000.0
capacity_solar = float(sys.argv[5]) * 1000.0
capacity_storage = float(sys.argv[6]) * 1000.0
capacity_biogas = float(sys.argv[7]) * 1000.0

capacity_storage_methane = 270000000.0 # 270TWht

print("Reading generation data from %s" % data_filename)

print("Simulating direct generation for:")
print("  %5.1fMW of onshore wind," % capacity_onshore)
print("  %5.1fMW of offshore wind," % capacity_offshore)
print("  %5.1fMW of photovoltaics," % capacity_solar)
print("  %5.1fMWh of grid storage," % capacity_storage)

data_file = open(data_filename, mode='r')
data_reader = csv.DictReader(data_file)

average_difference = 0.0
average_days = 0
wasted_total = 0.0
missing_total = 0.0

storage = 0.0
storage_methane = 90 * 24 * 0.9 * capacity_biogas

while True:
    data = next(data_reader, None)
    if (data == None):
        break
    #print(data)

    onshore = capacity_onshore * float(data['Wind onshore actual'])
    offshore = capacity_offshore * float(data['Wind offshore actual'])
    solar = capacity_solar * float(data['Photovoltaics actual'])
    methane = 0.90 * capacity_biogas

    month = int(data['Date'][5:7])
    if ((month in [10, 11, 12, 01, 02, 03]) and
        (storage < 100000000.0)):
        biogas_power = 0.50 * methane

        if (storage_methane > 0):
            draw = 0.95 * methane
            if (draw > storage_methane):
                draw = storage_methane
            biogas_power += 0.50 * draw
            storage_methane -= draw
    else:
        biogas_power = 0.0
        storage_methane += methane

    total = onshore + offshore + solar + biogas_power
    load = float(data['Load actual']) * load_factor
    difference = total - load

    average_difference += difference
    average_days += 1

    wasted = 0.0
    missing = 0.0
    if (difference >= 0):
        if (storage + (0.95 * difference) > capacity_storage):
            wasted = difference - ((capacity_storage - storage) / 0.95)
            wasted_total += wasted
            storage = capacity_storage
        else:
            storage += 0.95 * difference
    else:
        if ((storage * -0.95) > difference):
            missing = (storage * -0.95) - difference
            missing_total += missing
            storage = 0
        else:
            storage += difference / 0.95

    if (missing):
        print("%s %s: %9.2fMW + %9.2fMW + %9.2fMW + %9.2fMW = %10.2fMW of %10.2fMW (%10.2fMW): "
              "battery %10.2fMWh (%6.2f%%) stored, methane %10.2fGWh : %10.2fMW missing" %
              (data['Date'], data['Time'], onshore, offshore, solar, biogas_power, total, load, difference,
               storage, storage / capacity_storage * 100.0, storage_methane, missing))
    elif (wasted):
        print("%s %s: %9.2fMW + %9.2fMW + %9.2fMW + %9.2fMW = %10.2fMW of %10.2fMW (%10.2fMW): "
              "battery %10.2fMWh (%6.2f%%) stored : methane %10.2fGWh : %10.2fMW wasted" %
              (data['Date'], data['Time'], onshore, offshore, solar, biogas_power, total, load, difference,
               storage, storage / capacity_storage * 100.0, storage_methane, wasted))
    else:
        print("%s %s: %9.2fMW + %9.2fMW + %9.2fMW + %9.2fMW = %10.2fMW of %10.2fMW (%10.2fMW): "
              "battery %10.2fMWh (%6.2f%%) stored, methane %10.2fGWh" %
              (data['Date'], data['Time'], onshore, offshore, solar, biogas_power, total, load, difference,
               storage, storage / capacity_storage * 100.0, storage_methane))


print("Average difference is %9.2fMW" % (average_difference / average_days))
print("Missing %10.2fTWh, wasted %10.2fTWh" % (missing_total / 1000000.0, wasted_total / 1000000.0))
