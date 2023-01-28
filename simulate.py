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

import sys
import csv
import math

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
capacity_storage_battery_initial = 0.10
capacity_storage_battery_minimum_target = 0.10
storage_battery = capacity_storage_battery * capacity_storage_battery_initial

capacity_biomethane = float(sys.argv[8]) * 1000.0
capacity_biomethane_factor = 0.90
capacity_storage_methane = 270000000.0 # 270TWht
capacity_methane = float(sys.argv[9]) * 1000.0
capacity_methane_efficiency = 0.45
# give it a 3 months in the tank
storage_methane = 90 * 24 * 0.9 * capacity_biomethane

forecast_load_variation = 1.10
forecast_generation_variation = 0.90

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
print(" %8.1fGWh (%4.2f%%) 24h low battery target." %
      (capacity_storage_battery * capacity_storage_battery_minimum_target / 1000, capacity_storage_battery_minimum_target * 100))
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
average_hours = 0
wasted_total = 0.0
missing_total = 0.0

hours = 0
load_yearly = 0.0
hydro_yearly = 0.0
onshore_yearly = 0.0
offshore_yearly = 0.0
solar_yearly = 0.0
biomethane_yearly = 0.0
biomethane_power_yearly = 0.0
biomethane_burned_yearly = 0.0
wasted_yearly = 0.0
missing_yearly = 0.0

#
# Create a 24h forecast buffer
#
forecast_deficit_list = [0.0, ]
def forecast_deficit_list_add():
    global forecast_deficit_list

    data_forecast = next(data_forecast_reader, None)
    #print(data_forecast)

    load = float(data_forecast['Load']) * load_factor * forecast_load_variation

    generation = float(data_forecast['Hydropower']) * forecast_generation_variation
    generation += capacity_onshore * float(data_forecast['Wind onshore']) * forecast_generation_variation
    generation += capacity_offshore * float(data_forecast['Wind offshore']) * forecast_generation_variation
    generation += capacity_solar * float(data_forecast['Photovoltaics']) * forecast_generation_variation

    deficit = load - generation

    #print("%s %s: %6.2fMWh vs %6.2fMWh: %6.2fMWh missing" %
    #      (data_forecast['Date'], data_forecast['Time'], load, generation, deficit))

    forecast_deficit_list.append(deficit)

while (len(forecast_deficit_list) < 12):
    forecast_deficit_list_add()

#
# Try to average so we have the battery above 5% in 24h time, without
# a gap in between.
#
def biomethane_power_needed():
    global storage_battery
    global capacity_storage_battery_discharge_efficiency
    global forecast_deficit_list
    global capacity_storage_battery
    global capacity_storage_battery_minimum_target

    deficit_total = 0.0
    time_total = 0
    deficit_max = 0.0
    time_max = 1.0


    # make sure we never run out.
    for deficit in forecast_deficit_list:
        deficit_total += deficit
        time_total += 1

        if (deficit_max <= deficit_total):
            deficit_max = deficit_total
            time_max = time_total

    #print("Total deficit is %6.2fMWh in %dh (%6.2fMW)" %(deficit_total, time_total, deficit_total / time_total))
    #print("Maximum deficit is %6.2fMWh after %dh (%6.2fMW needed)" % (deficit_max, time_max, deficit_max / time_max))

    battery = storage_battery * capacity_storage_battery_discharge_efficiency
    #print("battery energy available: %6.2fMWh" % (battery))

    battery_goal = capacity_storage_battery * capacity_storage_battery_minimum_target * capacity_storage_battery_discharge_efficiency
    #print("battery energy goal: %6.2fMWh" % (battery_goal))

    if (deficit_max <= 0.0): # both deficit and deficit max are below zero.
        return 0

    methane_missing = (deficit_max - battery) / time_max
    #print("Methane missing to not run out: %6.2fMW" % (methane_missing))
    methane_goal = (deficit_total + battery_goal - battery) / time_total
    #print("Methane missing to keep battery useful: %6.2fMW" % (methane_goal))

    if (methane_missing > methane_goal):
        if (methane_missing > 0.0):
            return math.ceil(methane_missing / 1000) * 1000
        else:
            return 0.0
    else:
        if (methane_goal > 0.0):
            return math.ceil(methane_goal / 1000) * 1000
        else:
            return 0.0

#print ("Biomethane needed %6.2fGW" % (biomethane_power_needed()))

while True:
    hours += 1

    data_actual = next(data_actual_reader, None)
    if (data_actual == None):
        break
    #print(data_actual)

    date = data_actual['Date']
    load = float(data_actual['Load']) * load_factor
    hydro = float(data_actual['Hydropower'])
    onshore = capacity_onshore * float(data_actual['Wind onshore'])
    offshore = capacity_offshore * float(data_actual['Wind offshore'])
    solar = capacity_solar * float(data_actual['Photovoltaics'])
    biomethane = capacity_biomethane_factor * capacity_biomethane

    load_yearly += load
    hydro_yearly += hydro
    onshore_yearly += onshore
    offshore_yearly += offshore
    solar_yearly += solar

    forecast_deficit_list.pop(0)
    forecast_deficit_list_add()
    biomethane_power = biomethane_power_needed()
    if (biomethane_power > capacity_methane):
        biomethane_power = capacity_methane

    biomethane_burned = biomethane_power / capacity_methane_efficiency

    if (biomethane_burned):
        if ((storage_methane + biomethane) < biomethane_burned):
            biomethane_burned = storage_methane + biomethane
            biomethane_power = biomethane_burned * capacity_methane_efficiency
            storage_methane = 0
        else:
            storage_methane += biomethane - biomethane_burned
    else:
        storage_methane += biomethane

    if (storage_methane > capacity_storage_methane):
        storage_methane = capacity_storage_methane

    biomethane_yearly += biomethane
    biomethane_power_yearly += biomethane_power
    biomethane_burned_yearly += biomethane_burned

    total = hydro + onshore + offshore + solar + biomethane_power
    difference = total - load

    average_difference += difference
    average_hours += 1

    battery_flow = 0.0
    wasted = 0.0
    missing = 0.0
    if (difference >= 0):
        if (storage_battery + (capacity_storage_battery_charge_efficiency * difference) > capacity_storage_battery):
            battery_flow = (capacity_storage_battery - storage_battery) / capacity_storage_battery_charge_efficiency
            storage_battery = capacity_storage_battery
            wasted = difference - battery_flow
            wasted_yearly += wasted
            wasted_total += wasted
        else:
            battery_flow = capacity_storage_battery_charge_efficiency * difference
            storage_battery += battery_flow
    else:
        if ((storage_battery * -capacity_storage_battery_discharge_efficiency) > difference):
            battery_flow = -storage_battery * capacity_storage_battery_discharge_efficiency
            missing = -(difference + battery_flow)
            missing_yearly += missing
            missing_total += missing
            storage_battery = 0
        else:
            battery_flow = difference / capacity_storage_battery_discharge_efficiency
            storage_battery += battery_flow

    print("%s %s: Storage:  Battery: %4.2fTWh (%6.2f%%), Methane: %6.2fTWh (%6.2f%%)." %
          (date, data_actual['Time'], storage_battery / 1000000, 100.0 * storage_battery / capacity_storage_battery,
           storage_methane / 1000000, 100 * storage_methane / 270000000))

    if (missing):
        print("\t%6.2fGW: %4.2fGW + %6.2fGW + %6.2fGW + %6.2fGW + %7.2fGW + %6.2fGW: %6.2fGW missing" %
              (load / 1000, hydro / 1000, onshore / 1000, offshore / 1000, solar / 1000,
               - battery_flow / 1000, biomethane_power / 1000, missing / 1000))
    elif (wasted):
        print("\t%6.2fGW: %4.2fGW + %6.2fGW + %6.2fGW + %6.2fGW + %7.2fGW + %6.2fGW: %6.2fGW wasted" %
              (load / 1000, hydro / 1000, onshore / 1000, offshore / 1000, solar / 1000,
               - battery_flow / 1000, biomethane_power / 1000, wasted / 1000))
    else:
        print("\t%6.2fGW: %4.2fGW + %6.2fGW + %6.2fGW + %6.2fGW + %7.2fGW + %6.2fGW" %
              (load / 1000, hydro / 1000, onshore / 1000, offshore / 1000, solar / 1000,
               - battery_flow / 1000, biomethane_power / 1000))

    if (date.endswith("-12-31") and data_actual['Time'] == "23:00"):
        print("")
        print("%s: %ddays" % (date[0:4], hours / 24))
        print("%6.2fTWh total load, %6.2fGWh average daily load, %4.2fGWh average hourly load." %
              (load_yearly / 1000000, 24 * load_yearly / hours / 1000, load_yearly / hours / 1000))
        print("Missing %6.2fTWh, wasted %6.2fTWh" % (missing_yearly / 1000000.0, wasted_yearly / 1000000.0))
        print("Hydro %6.2fTWh, Onshore %6.2fTWh, Offshore %6.2fTWh, Solar %6.2fTWh, Methane %6.2fTWh." %
              (hydro_yearly / 1000000, onshore_yearly / 1000000, offshore_yearly / 1000000,
               solar_yearly / 1000000, biomethane_power_yearly / 1000000))
        print("Methane: %6.2fTWh (%6.2fGW) produced, %6.2fTWh (%6.2fGW) burned, current storage %6.2fTWh (%6.2f%%)." %
              (biomethane_yearly / 1000000, biomethane_yearly / hours / 1000,
               biomethane_burned_yearly / 1000000, biomethane_burned_yearly / hours / 1000,
               storage_methane / 1000000, 100 * storage_methane / 270000000))


        missing_yearly = 0.0
        wasted_yearly = 0.0

        print("")

        load_yearly = 0.0
        hydro_yearly = 0.0
        onshore_yearly = 0.0
        offshore_yearly = 0.0
        solar_yearly = 0.0
        biomethane_yearly = 0.0
        biomethane_power_yearly = 0.0
        biomethane_burned_yearly = 0.0

        hours = 0

        # we will need forecast data soon.
        if (date[0:4] == "2022"):
            break

print("Totals:")
print("Average hourly difference between renewables and grid load is %6.2fGW" % (average_difference / average_hours))
print("Missing %6.2fTWh, wasted %6.2fTWh" % (missing_total / 1000000.0, wasted_total / 1000000.0))
