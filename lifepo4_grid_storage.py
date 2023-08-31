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

print("")
print("Analysing the effect of %4.2fGWh of grid scale battery storage over a period of %d years..." %
      (capacity_original / 1000.0, duration))
print("")

#
# Calculates depth-of-discharge, keeps track of volume shifted, and
# then degrades the battery capacity accordingly.
#
def cycle(date, cycle_volume):
    global capacity
    global volume_total
    global days_short

    # Battery round-trip is 90% efficient, mostly inverter losses.
    # But this is round-trip, so when charging it is 5%.
    # When discharging, 5% of actual battery capacity is lost again.
    #
    # For reference, Tesla claims a 93.5% round trip efficiency for
    # their megapacks at .25C. (4h for a full discharge)
    # https://electrek.co/2022/09/14/tesla-megapack-update-specs-price/
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

#
# Cycles through the available consumption data until the requested number
# of years is reached.
#
while True:
    with open(consumption_filename, mode='r') as consumption_file:
        consumption_reader = csv.DictReader(consumption_file)
        for consumption in consumption_reader:
            date = consumption['Date']

            if (date.endswith("-01-01")):
                print("year %2d: using data from %s..." % (years, date[0:4]))

            cycle(date, float(consumption['Storage Cycle [MWh]']))

            days += 1
            if (date.endswith("-12-31")):
                years += 1
                if (years >= duration):
                    break
    if (years >= duration):
        break

print("")

#
#
#
print("After %d years (%d days), a total of %9.2fGWh was cycled through." %
      ((days / 365), days, volume_total / 1000.0))
print("On average, %5.2fGWh was cycled through each day, equivalent to %.2f full charges (%2.2f%%)." %
      (volume_total / days / 1000.0, volume_total / capacity_original, volume_total / capacity_original / days * 100.0))
if (days_short):
    print("On %d days, the available storage was insufficient to level out the grid load (%2.2f%%)." %
          (days_short, 100.0 * days_short / days))
print("The capacity of these LiFePO4 batteries will have degraded by %4.2fGWh to %4.2fGWh (%2.2f%%)." %
      ((capacity_original - capacity) / 1000.0, capacity / 1000.0,  100.0 * capacity / capacity_original))
print("Total energy loss of storing electricity in these batteries amounted to %8.2fGWh (10%%)." % (volume_total / 10000.0))
print("An average increase in generation capacity of %6.2fMW is needed to compensate for this loss." %
      (volume_total / days / 240.0))
print("")

print("Cost analysis...")
print("")

# Status 20230831: https://www.tesla.com/megapack/design
print("Tesla Megapacks (LiFePO4, 2022): status 20230831")
capacity_known = 3854400.0 # kWh
cost_known = 1593272170.0 # usd
usd_to_eur = 0.92
# annual maintenance cost $4,966,480
# price escalates at 2% per year
print("\tInstalling 1000 4h duration Megapacks (%.2fMWh) costs %.2fM usd." %
      (capacity_known / 1000.0, cost_known / 1000000.0))
cost_per_kwh_tesla = cost_known * usd_to_eur / capacity_known
print("\tThe cost per GWh is %5.2fM EUR." %
      (cost_per_kwh_tesla))
cost_total = cost_per_kwh_tesla * capacity_original
print("\t%5.2fGWh of grid level storage costs %2.2fB EUR." %
      (capacity_original / 1000.0, cost_total / 1000000.0))
maintenance_cost_tesla = 4966480
maintenance_cost_increase_tesla = .02
print("\tMaintaining 1000 Megapacks costs %1.2fM usd yearly, with an increase of %1.1f%% per year." %
      (maintenance_cost_tesla / 1000000.0, maintenance_cost_increase_tesla * 100))
maintenance_cost_base = (maintenance_cost_tesla * usd_to_eur / capacity_known * capacity_original)
maintenance_cost_tesla_total = 0.0
for year in range(0, duration):
    maintenance_cost_tesla_total += (maintenance_cost_base * ((1 + maintenance_cost_increase_tesla) ** year))
print("\tMaintaining %5.2fGWh over %d years costs %3.2fM EUR in maintenance" %
      (capacity_original / 1000.0, duration, maintenance_cost_tesla_total / 1000))
cost_per_kwh_delivered_tesla = (cost_total + maintenance_cost_tesla_total) * 100 / volume_total
print("\tOver %d years, the cost per MWh cycled is %3.2fEUR, or %3.2fcents per kWh." %
      (years, cost_per_kwh_delivered_tesla * 10, cost_per_kwh_delivered_tesla))
print("")


# Status 20230829: https://www.gobelpower.com/gobel-power-gpsr1pc200-512v-280ah-lifepo4-battery_p114.html
capacity_known = 15.36 # kWh
cost_known = 2431.0 # eur
print("Server rack batteries (Gobel Power, 15.36kWh): status 20230829")
print("\tA single %2.2fkWh server rack battery costs %.2fk EUR, when bought online in china." %
      (capacity_known, cost_known / 1000.0))
cost_per_kwh_rack = cost_known / capacity_known
print("\tThe cost per GWh is %5.2fM EUR." %
      (cost_per_kwh_rack))
cost_total = cost_per_kwh_rack * capacity_original
print("\t%5.2fGWh of grid level storage costs %2.2fB EUR." %
      (capacity_original / 1000.0, cost_total / 1000000.0))
cost_per_kwh_delivered_rack = cost_total * 100 / volume_total
print("\tOver %d years, the cost per MWh cycled is %3.2fEUR, or %3.2fcents per kWh." %
      (years, cost_per_kwh_delivered_rack * 10, cost_per_kwh_delivered_rack))
print("")

# Status 20230831: https://qiso.en.alibaba.com/
# Eve LF-280K, 500+ pieces, delivered from within the EU: 73.02EUR
capacity_known = 3.2 * .28 # kWh
cost_known = 73.02 # eur
print("Raw LiFePO4 cells (Eve LF-280k, 280Ah, from Qiso): status 20230831")
print("\tA single %3.2fWh raw LiFePO4 cell costs %.2f EUR, for a minimum of 500 units, shipped from within the EU." %
      (capacity_known * 1000.0, cost_known))
cost_per_kwh_raw = cost_known / capacity_known
print("\tThe cost per GWh is %5.2fM EUR." %
      (cost_per_kwh_raw))
cost_total = cost_per_kwh_raw * capacity_original
print("\t%5.2fGWh of grid level storage costs %2.2fB EUR." %
      (capacity_original / 1000.0, cost_total / 1000000.0))
cost_per_kwh_delivered_raw = cost_total * 100 / volume_total
print("\tOver %d years, the cost per MWh cycled is %3.2fEUR, or %3.2fcents per kWh." %
      (years, cost_total * 1000 / volume_total, cost_total * 100 / volume_total))

print("")
print("While the server rack batteries and raw cells might at first not seem relevant,")
print("their overal cost and cost per kWh cycled are good future cost datapoints.")
print("")
print("Tesla Megapacks are sold out 2 years into the future, and the margins are going")
print("to be enormous. Yet they still only cost %3.2fEUR per kWh of storage, or" % (cost_per_kwh_tesla))
print("%3.2fcents per kWh delivered for a %5.2fGWh install over %d years." %
      (cost_per_kwh_delivered_tesla, capacity_original / 1000.0, duration))
print("")
print("While a server rack battery has only cells, a bms, the container and some cables,")
print("given the enormous demand, it is a good metric for where the price for actual grid")
print("scale storage should be today without a Tesla markup.")
print("")
print("Raw LiFePO4 cells are astoundingly good value, even with customs and shipping to")
print("germany included. And yet, the actual price, today, for manufacturing such cells is")
print("going to be half still. At %5.2fEUR per kWh of capacity, and a cycle cost of %3.2fcents"
      % (cost_per_kwh_raw, cost_per_kwh_delivered_raw))
print("per kWh delivered, it is where the cost of grid level storage will be, all in,")
print("several years in the future, when supply matches demand more closely.")

print("")
# status december 1st 2021: https://www.lowcarboncontracts.uk/cfds/hinkley-point-c
strike_price_hinkley_gbp = 106.12
gbp_to_eur = 1.12 # 20221230
print("Even at %3.2fEUR/MWh delivered, an expensive Tesla megapack compares favourably compared\n"
      "to the nuclear power plant (EDFs EPR) being built at Hinkley Point C, which has\n"
      "a strike price of %3.2fEUR/MWh (%3.2fGBP/MWh in 2022). This is especially striking given\n"
      "that battery storage does double duty, and a nuclear power plant is only financially viable\n"
      "at a given high constant baseload over its lifetime." %
      (cost_per_kwh_delivered_tesla * 10, strike_price_hinkley_gbp * gbp_to_eur, strike_price_hinkley_gbp))
