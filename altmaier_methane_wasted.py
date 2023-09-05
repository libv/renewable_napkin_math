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

if (len(sys.argv) != 4):
    print("Error: Wrong number of arguments.")
    print("%s <generation csv> <day ahead methane pricing csv> "
          "<capacity missing csv>" % (sys.argv[0]))
    sys.exit()

generation_filename = sys.argv[1]
price_filename = sys.argv[2]
missing_filename = sys.argv[3]

year_start = 2017

# open generation, and find the first entry of our requested year
generation_file = open(generation_filename, mode='r')
generation_reader = csv.DictReader(generation_file)
generation_entry = None

while True:
    generation_entry = next(generation_reader, None)
    if (generation_entry == None):
        print("Failed to find %d in %s.\n" % (year_start, generation_filename))
        sys.exit()

    if (int(generation_entry['Date'][0:4]) == year_start):
        break

# open methane day ahead pricing, and find the first entry of our requested year
price_file = open(price_filename, mode='r')
price_reader = csv.DictReader(price_file)
price_entry = None

while True:
    price_entry = next(price_reader, None)
    if (price_entry == None):
        print("Failed to find %d in %s.\n" % (year_start - 1, price_filename))
        sys.exit()

    if (int(price_entry['Date'][0:4]) == year_start):
        break

# open capacity missing csv, and find the entry of the previous year
missing_file = open(missing_filename, mode='r')
missing_reader = csv.DictReader(missing_file)
missing_entry = None

while True:
    missing_entry = next(missing_reader, None)
    if (missing_entry == None):
        print("Failed to find %d in %s.\n" % (year_start - 1, missing_filename))
        sys.exit()

    if (int(missing_entry['Year'][0:4]) == (year_start - 1)):
        break

print("If the artificial neutering of renewables by the SPD and CDU/CSU had not")
print("happened in 2012 (aka. Altmaier Knick), how much methane would we have been")
print("able to offset, and how much would this methane have cost in day ahead pricing?")

print("")

methane_used_total = 0.0
methane_offset_total = 0.0
methane_used_cost_total = 0.0
methane_offset_cost_total = 0.0

def methane_missing_yearly(year, solar_factor, solar_factor_adjustment,
                           onshore_factor, onshore_factor_adjustment,
                           offshore_factor, offshore_factor_adjustment):
    global generation_entry
    global price_entry
    global methane_used_total
    global methane_offset_total
    global methane_used_cost_total
    global methane_offset_cost_total

    methane_used_yearly = 0.0
    methane_offset_yearly = 0.0
    methane_used_cost_yearly = 0.0
    methane_offset_cost_yearly = 0.0

    print("Calculating for %s:" % year)

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
                cost = float(price_entry['Weighted Price EUR/MWh'])
                cost_used = methane_used_day * cost
                cost_offset = methane_offset_day * cost

                print("%s: %6.2fGWh of %6.2fGWh (%6.2f%%): %6.2fM EUR of %6.2fM EUR" %
                      (day, methane_offset_day / 1000, methane_used_day / 1000,
                       100.0 * methane_offset_day / methane_used_day,
                       cost_offset / 1000000.0, cost_used / 1000000.0))

                methane_offset_yearly += methane_offset_day
                methane_used_yearly += methane_used_day
                methane_used_cost_yearly += cost_used
                methane_offset_cost_yearly += cost_offset

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
        if (int(generation_entry['Date'][0:4]) != year):
            break

        solar_factor += solar_factor_adjustment
        onshore_factor += onshore_factor_adjustment
        offshore_factor += offshore_factor_adjustment

    print("")
    print("%d:" % (year))
    print(" %7.3fTWh of %7.3fTWh of methane could have been offset (%5.2f%%)." %
      (methane_offset_yearly / 1000000, methane_used_yearly / 1000000,
       100 * methane_offset_yearly / methane_used_yearly))
    print(" %5.2fB EUR of %5.2fB EUR at day-ahead market prices could have been saved (%5.2f%%)." %
      (methane_offset_cost_yearly / 1000000000.0,
       methane_used_cost_yearly / 1000000000.0,
       100 * methane_offset_cost_yearly / methane_used_cost_yearly))
    print("")

    methane_used_total += methane_used_yearly
    methane_offset_total += methane_offset_yearly
    methane_used_cost_total += methane_used_cost_yearly
    methane_offset_cost_total += methane_offset_cost_yearly

year = year_start
while True:
    solar_factor = float(missing_entry['Solar Missing Fraction'])
    onshore_factor = float(missing_entry['Wind onshore Missing Fraction'])
    offshore_factor = float(missing_entry['Wind offshore Missing Fraction'])

    missing_entry = next(missing_reader, None)
    if (missing_entry == None):
        break

    solar_factor_next = float(missing_entry['Solar Missing Fraction'])
    onshore_factor_next = float(missing_entry['Wind onshore Missing Fraction'])
    offshore_factor_next = float(missing_entry['Wind offshore Missing Fraction'])

    if ((year % 4) == 0):
        days = 366.0
    else:
        days = 365.0

    solar_factor_adjustment = (solar_factor_next - solar_factor) / days
    onshore_factor_adjustment = (onshore_factor_next - onshore_factor) / days
    offshore_factor_adjustment = (offshore_factor_next - offshore_factor) / days

    methane_missing_yearly(year, solar_factor, solar_factor_adjustment,
                           onshore_factor, onshore_factor_adjustment,
                           offshore_factor, offshore_factor_adjustment)
    year += 1

print("Between %d and %d:" % (year_start, year))
print(" %7.3fTWh of %7.3fTWh of methane could have been offset (%5.2f%%)." %
      (methane_offset_total / 1000000, methane_used_total / 1000000,
       100 * methane_offset_total / methane_used_total))
print(" %5.2fB EUR of %5.2fB EUR at day-ahead market prices could have been saved (%5.2f%%)." %
      (methane_offset_cost_total / 1000000000.0,
       methane_used_cost_total / 1000000000.0,
       100 * methane_offset_cost_total / methane_used_cost_total))
print("")
