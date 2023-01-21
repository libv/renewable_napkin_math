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

if (len(sys.argv) != 10):
    print("Error: Wrong number of arguments.")
    print("%s <forecast data csv> <actual data csv>  <load factor> <onshore wind GW> <offshore wind GW> "
          "<solar GW> <battery storage GWh> <biomethane GW> <methane GW>" %
          (sys.argv[0]))
    sys.exit()

data_forecast_filename = sys.argv[1]
data_actual_filename = sys.argv[2]

load_factor = float(sys.argv[3])

capacity_onshore = float(sys.argv[4]) * 1000.0
capacity_offshore = float(sys.argv[5]) * 1000.0
capacity_solar = float(sys.argv[6]) * 1000.0

capacity_storage_battery = float(sys.argv[7]) * 1000.0
capacity_storage_battery_charge_efficiency = 0.95
capacity_storage_battery_discharge_efficiency = 0.95
capacity_storage_battery_initial = 0.05
storage_battery = capacity_storage_battery * capacity_storage_battery_initial

capacity_biomethane = float(sys.argv[8]) * 1000.0
capacity_biomethane_factor = 0.90
capacity_storage_methane = 270000000.0 # 270TWht
capacity_methane = float(sys.argv[9]) * 1000.0
capacity_methane_efficiency = 0.45
# give it a 3 months in the tank
storage_methane = 90 * 24 * 0.9 * capacity_biomethane

print("Simulating direct generation for:")
print("")
print("    %4.2fx grid load over historic data." % (load_factor))
print("")
print("    %5.1fGW  of onshore wind generation capacity," % (capacity_onshore / 1000))
print("    %5.1fGW  of offshore wind generation capacity," % (capacity_offshore / 1000))
print("    %5.1fGW  of photovoltaic generation capacity," % (capacity_solar / 1000))
print("")
print(" %8.1fGWh of grid level battery storage (efficiency: %4.2f%%/%4.2f%% Charge/Discharge)," %
      (capacity_storage_battery / 1000, capacity_storage_battery_charge_efficiency * 100,
       capacity_storage_battery_discharge_efficiency * 100))
print(" %8.1fGWh stored initially (%4.2f%%)" % (storage_battery / 1000, capacity_storage_battery_initial * 100))
print("")
print("    %5.1fGW  of biomethane production (%4.2f%% capacity factor)," %
      (capacity_biomethane / 1000, capacity_biomethane_factor * 100))
print(" %8.1fGWh of geological methane storage capacity," % (capacity_storage_methane / 1000))
print(" %8.1fGWh of methane stored initially (%4.2f%%)," % (storage_methane / 1000, 100 * storage_methane / capacity_storage_methane))
print("    %5.1fGW  of methane electricity generation capacity (%4.2f%% electrical efficiency)," %
      (capacity_methane / 1000, capacity_methane_efficiency * 100))
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
    biomethane = capacity_biomethane_factor * capacity_biomethane

    month = int(date[5:7])
    if ((month in [10, 11, 12, 01, 02, 03]) and
        (storage_battery < 100000000.0)):
        biomethane_power = capacity_methane_efficiency * biomethane

        if (storage_methane > 0):
            draw = biomethane
            if (draw > storage_methane):
                draw = storage_methane
            biomethane_power += capacity_methane_efficiency * draw
            storage_methane -= draw
    else:
        biomethane_power = 0.0
        storage_methane += biomethane

    total = hydro + onshore + offshore + solar + biomethane_power
    load = float(data_actual['Load']) * load_factor
    difference = total - load

    average_difference += difference
    average_days += 1

    wasted = 0.0
    missing = 0.0
    if (difference >= 0):
        if (storage_battery + (capacity_storage_battery_charge_efficiency * difference) > capacity_storage_battery):
            wasted = difference - ((capacity_storage_battery - storage_battery) / capacity_storage_battery_charge_efficiency)
            wasted_yearly += wasted
            wasted_total += wasted
            storage_battery = capacity_storage_battery
        else:
            storage_battery += capacity_storage_battery_charge_efficiency * difference
    else:
        if ((storage_battery * -capacity_storage_battery_discharge_efficiency) > difference):
            missing = (storage_battery * -capacity_storage_battery_discharge_efficiency) - difference
            missing_yearly += missing
            missing_total += missing
            storage_battery = 0
        else:
            storage_battery += difference / capacity_storage_battery_discharge_efficiency

    print("%s %s: Storage:  Battery: %4.2fTWh (%6.2f%%), Methane: %5.2fTWh (%6.2f%%)." %
          (date, data_actual['Time'], storage_battery / 1000000, 100.0 * storage_battery / capacity_storage_battery,
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
