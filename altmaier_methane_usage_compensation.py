#! /usr/bin/python

# 2022 was a terrible year for many reasons.
#
# Fossil gas prices were insane, and this in turn made the german
# electricity prices twice as insane.
#
# What if we calculated the extra gas usage caused by the lack of installed
# renewable capacity caused by the Altmaier knick and other effects of the
# very bad policies of the CDU/CSU and SPD in the 2010s?
#
# We can also add in the day ahead trading cost of said gas to try to put
# a pricetag on this.
#
# We could try calculate out the actual demand versus generation and offset
# only the methane used for actual germany internal demand. But thanks to the
# merit-order system the cost of electricity is the cost of all electricity
# and import/export of electricity over the year is more or less in balance.
#
import sys
import csv

if (len(sys.argv) != 7):
    print("Error: Wrong number of arguments.")
    print("%s <generation csv> <day ahead methane pricing csv> "
          "<year> <solar factor> <onshore wind factor> <offshore wind factor>"
          % (sys.argv[0]))
    sys.exit()

generation_filename = sys.argv[1]
price_filename = sys.argv[2]
year_requested = int(sys.argv[3])
solar_factor = float(sys.argv[4])
onshore_factor = float(sys.argv[5])
offshore_factor = float(sys.argv[6])

# open generation, and find the first entry of our requested year
generation_file = open(generation_filename, mode='r')
generation_reader = csv.DictReader(generation_file)
generation_entry = None

while True:
    generation_entry = next(generation_reader, None)
    if (generation_entry == None):
        print("Failed to find %d in %s.\n" % (year, generation_filename))
        sys.exit()

    if (int(generation_entry['Date'][0:4]) == year_requested):
        break

# open methane day ahead pricing, and find the first entry of our requested year
price_file = open(price_filename, mode='r')
price_reader = csv.DictReader(price_file)
price_entry = None

while True:
    price_entry = next(price_reader, None)
    if (price_entry == None):
        print("Failed to find %d in %s.\n" % (year, price_filename))
        sys.exit()

    if (int(price_entry['Date'][0:4]) == year_requested):
        break

methane_offset_year = 0.0
methane_used_year = 0.0
methane_used_cost_year = 0.0
methane_offset_cost_year = 0.0

while True:
    day = generation_entry['Date']
    methane_offset_day = 0.0
    methane_used_day = 0.0

    while True:
        methane = float(generation_entry['Fossil gas [MWh]'])

        solar = float(generation_entry['Photovoltaics [MWh]'])
        onshore = float(generation_entry['Wind onshore [MWh]'])
        offshore = float(generation_entry['Wind offshore [MWh]'])

        #print("%s %s: %8.2fMWh + %8.2fMWh + %8.2fMWh vs %8.2fMWh" %
        #      (day, generation_entry['Start'], solar, onshore, offshore, methane))

        solar *= solar_factor
        onshore *= onshore_factor
        offshore *= offshore_factor

        total = solar + onshore + offshore

        if (total >= methane):
            offset = methane
        else:
            offset = total

        #print("\t%8.2fMWh + %8.2fMWh + %8.2fMWh = %8.2fMWh: %8.2fMWh offset" %
        #      (solar, onshore, offshore, total, offset))

        methane_offset_day += 2 * offset
        methane_used_day += 2 * methane

        if (generation_entry['Start'] == "23:00"):
            print("%s: %9.2fMWh of %9.2fMWh saved (%5.2f%%)." %
                  (day, methane_offset_day, methane_used_day,
                   100.0 * methane_offset_day / methane_used_day))

            cost = float(price_entry['Weighted Price EUR/MWh'])
            cost_used = methane_used_day * cost
            cost_offset = methane_offset_day * cost
            print("  Cost: %9.2fMEUR of %9.2fMEUR saved." %
                  (cost_offset / 1000000.0, cost_used / 1000000.0))

            methane_offset_year += methane_offset_day
            methane_used_year += methane_used_day
            methane_used_cost_year += cost_used
            methane_offset_cost_year += cost_offset

        generation_entry = next(generation_reader, None)
        if (generation_entry == None):
            break
        if (generation_entry['Start'] == "00:00"):
            break

    if (generation_entry == None):
        break
    price_entry = next(price_reader, None)
    if (price_entry == None):
        break
    if (int(generation_entry['Date'][0:4]) != year_requested):
        break


print("%d: %8.2fGWh of %8.2fGWh saved (%5.2f%%)." %
      (year_requested, methane_offset_year / 1000,
       methane_used_year / 1000,
       100 * methane_offset_year / methane_used_year))
print("\t Cost: %9.2fBEUR of %9.2fBEUR saved." %
      (methane_offset_cost_year / 1000000000.0,
       methane_used_cost_year / 1000000000.0))
