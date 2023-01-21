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

if (len(sys.argv) != 9):
    print("Error: Wrong number of arguments.")
    print("%s <forecast data csv> <actual data csv>  <load factor> <onshore wind GW> <offshore wind GW> <solar GW> <biomethane GW> <storage GWh>" %
          (sys.argv[0]))
    sys.exit()

data_forecast_filename = sys.argv[1]
data_actual_filename = sys.argv[2]
load_factor = float(sys.argv[3])
capacity_onshore = float(sys.argv[4]) * 1000.0
capacity_offshore = float(sys.argv[5]) * 1000.0
capacity_solar = float(sys.argv[6]) * 1000.0
capacity_biomethane = float(sys.argv[7]) * 1000.0
capacity_storage_battery = float(sys.argv[8]) * 1000.0

capacity_storage_methane = 270000000.0 # 270TWht

print("Simulating direct generation for:")
print("")
print("    %4.2fx grid load over historic data." % (load_factor))
print("")
print("    %5.1fGW  of onshore wind," % (capacity_onshore / 1000))
print("    %5.1fGW  of offshore wind," % (capacity_offshore / 1000))
print("    %5.1fGW  of photovoltaics," % (capacity_solar / 1000))
print("    %5.1fGW  of biomethane production," % (capacity_biomethane / 1000))
print("")
print(" %8.1fGWh of grid level battery storage," % (capacity_storage_battery / 1000))
print(" %8.1fGWh of geological methane storage," % (capacity_storage_methane / 1000))
print("")
print("Retrieving forecast data from %s" % data_forecast_filename)
print("Retrieving actual data from %s" % data_actual_filename)
print("")

data_forecast_file = open(data_forecast_filename, mode='r')
data_forecast_reader = csv.DictReader(data_forecast_file)

data_actual_file = open(data_actual_filename, mode='r')
data_actual_reader = csv.DictReader(data_actual_file)

average_difference = 0.0
average_days = 0
wasted_total = 0.0
missing_total = 0.0

wasted_yearly = 0.0
missing_yearly = 0.0

storage = 0.0

# give it a 3 months in the tank
storage_methane = 90 * 24 * 0.9 * capacity_biomethane

while True:
    data_actual = next(data_actual_reader, None)
    if (data_actual == None):
        break
    #print(data_actual)

    date = data_actual['Date']
    hydro = float(data_actual['Hydropower'])
    onshore = capacity_onshore * float(data_actual['Wind onshore'])
    offshore = capacity_offshore * float(data_actual['Wind offshore'])
    solar = capacity_solar * float(data_actual['Photovoltaics'])
    methane = 0.90 * capacity_biomethane

    month = int(date[5:7])
    if ((month in [10, 11, 12, 01, 02, 03]) and
        (storage < 100000000.0)):
        biomethane_power = 0.50 * methane

        if (storage_methane > 0):
            draw = 0.95 * methane
            if (draw > storage_methane):
                draw = storage_methane
            biomethane_power += 0.50 * draw
            storage_methane -= draw
    else:
        biomethane_power = 0.0
        storage_methane += methane

    total = hydro + onshore + offshore + solar + biomethane_power
    load = float(data_actual['Load']) * load_factor
    difference = total - load

    average_difference += difference
    average_days += 1

    wasted = 0.0
    missing = 0.0
    if (difference >= 0):
        if (storage + (0.95 * difference) > capacity_storage_battery):
            wasted = difference - ((capacity_storage_battery - storage) / 0.95)
            wasted_yearly += wasted
            wasted_total += wasted
            storage = capacity_storage_battery
        else:
            storage += 0.95 * difference
    else:
        if ((storage * -0.95) > difference):
            missing = (storage * -0.95) - difference
            missing_yearly += missing
            missing_total += missing
            storage = 0
        else:
            storage += difference / 0.95

    print("%s %s: Storage:  Battery: %4.2fTWh (%6.2f%%), Methane: %5.2fTWh (%6.2f%%)." %
          (date, data_actual['Time'], storage / 1000000, 100.0 * storage / capacity_storage_battery,
           storage_methane / 1000000, 100 * storage_methane / 270000000))

    if (missing):
        print("\t%6.2fGW: %4.2fGW + %6.2fGW + %6.2fGW + %6.2fGW + %6.2fGW: %6.2fGW missing" %
              (load / 1000, hydro / 1000, onshore / 1000, offshore / 1000, solar / 1000,
               biomethane_power / 1000, missing / 1000))
    elif (wasted):
        print("\t%6.2fGW: %4.2fGW + %6.2fGW + %6.2fGW + %6.2fGW + %6.2fGW: %6.2fGW wasted" %
              (load / 1000, hydro / 1000, onshore / 1000, offshore / 1000, solar / 1000,
               biomethane_power / 1000, wasted / 1000))
    else:
        print("\t%6.2fGW: %4.2fGW + %6.2fGW + %6.2fGW + %6.2fGW + %6.2fGW" %
              (load / 1000, hydro / 1000, onshore / 1000, offshore / 1000, solar / 1000,
               biomethane_power / 1000))

    if (date.endswith("-12-31") and data_actual['Time'] == "23:00"):
        print("")
        print("%s:" % (date[0:4]))
        print("Missing %6.2fTWh, wasted %6.2fTWh" % (missing_yearly / 1000000.0, wasted_yearly / 1000000.0))
        missing_yearly = 0.0
        wasted_yearly = 0.0

        print("")

        # we will need forecast data soon.
        if (date[0:4] == "2022"):
            break

print("Totals:")
print("Average difference is %6.2fGW" % (average_difference / average_days))
print("Missing %6.2fTWh, wasted %6.2fTWh" % (missing_total / 1000000.0, wasted_total / 1000000.0))
