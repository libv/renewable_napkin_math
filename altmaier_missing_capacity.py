#!/usr/bin/python

#
# There is a clear drop in new installations of solar after 2012,
# and 2017 for on and offshore wind. So take these peak values, and
# use that as new installated capacity for the following years, and
# calculate how much is missing.
#
# The data from smard only goes back to 2015 (capacity installed until the end
# of 2014). Data has been retrieved from other sources, and the numbers do not
# match, so we use the other sources' data, and calculate a factor of missing
# capacity. This will then scale the hourly generation values in our actual
# analysis.
#

import sys
import csv

# The data from 2000-2021 is from
# https://www.erneuerbare-energien.de/EE/Navigation/DE/Service/Erneuerbare_Energien_in_Zahlen/Zeitreihen/zeitreihen.html
# Dated September 2022.
#
# The 2022 data is from:
# https://www.iwr.de/news/trendwende-in-deutschland-sind-2022-knapp-10-000-mw-neue-wind-und-solarleistung-in-betrieb-gegangen-news38202
# Dated 20230113
#
data_years =    [ 2000,  2001,  2002,  2003,  2004,
                  2005,  2006,  2007,  2008,  2009,
                  2010,  2011,  2012,  2013,  2014,
                  2015,  2016,  2017,  2018,  2019,
                  2020,  2021,  2022]
data_solar =    [  114,   176,   296,   435,  1105,
                  2056,  2899,  4170,  6120, 10566,
                 18006, 25916, 34077, 36710, 37900,
                 39224, 40679, 42293, 45158, 48864,
                 53671, 59373, 66480]
data_onshore =  [ 6097,  8738, 11976, 14381, 16419,
                 18248, 20474, 22116, 22794, 25697,
                 26823, 28524, 30711, 32969, 37620,
                 41297, 45283, 50174, 52328, 53187,
                 54414, 56046, 58521]
data_offshore = [    0,     0,     0,     0,     0,
                     0,     0,     0,     0,    35,
                    80,   188,   268,   508,   994,
                  3283,  4152,  5406,  6393,  7555,
                  7787,  7787,  8129]

if (len(sys.argv) != 2):
    print("Error: Wrong number of arguments.")
    print("%s <result csv>" % (sys.argv[0]))
    sys.exit()

result_filename = sys.argv[1]

print(
"The CDU/CSU (catholics) and SPD (socialists) aka GroKo (Grosse Koalition),\nunder Angela Merkel, ruled Germany from 2013 til 2021. From 2005 til 2009,\nthe same GroKo ruled. And in the time between, they were joined by the\nliberals, a political party even more conducive to lobbying.")
print("")
print("During the 2000s, there was a massive boom in renewable installations, and a\nwhole new industry in germany had formed to create and install renewable\ncapacity. By around 2013, it was clear that renewable energy was not only\nearnest competition to fossil fuels, and the subsidies for new installed\ncapacity were starting to weigh heavily. So subsidies were massively reduced,\nand the industry was given quite a bit of uncertainty on the future of said\nsubsidies. The resulting 'Altmaier Knick' (Peter Altmaier, the responsible\nminister) saw new solar installations collapse almost immediately, and there\nis a clear similar trend with wind 5ys later.")
print("")
print("The collapse of onshore wind installations after 2017 is also attributable to\nthe actions of the Bavarian gouvernment, ruled by the CSU (catholics) and\nFreie Waehler (even more conservative than the CSU). Mainly the 10H rule (wind\nturbines need to be further away from populated areas than 10x the height of\nthe turbine) made it impossible to install new wind capacity.")
print("")
print("The result is the near total collapse of the renewable industry in germany,\nall solar producers and most of wind turbine construction collapsed, and their\nIP and remaining assets got gobbled up by foreign entities.")
print("")
print("This application calculates the capacity missing, if we flatline the peak new\ninstalled capacity in 2012 and 2017 respectively. Take note, the values are\nflatlined, and not extrapolated from previous growth ratios. This is the\nabsolute lowest estimate for what capacity is missing.")
print("")

year_solar_max = 2012
year_onshore_max = 2017
year_offshore_max = 2017

solar_max = 0.0
onshore_max = 0.0
offshore_max = 0.0

solar_missing = 0.0
onshore_missing = 0.0
offshore_missing = 0.0

result_file = open(result_filename, mode='w')
result_fieldnames = ['Year',
                     'Solar Installed',
                     'Solar Missing',
                     'Solar Missing Fraction',
                     'Wind onshore Installed',
                     'Wind onshore Missing',
                     'Wind onshore Missing Fraction',
                     'Wind offshore Installed',
                     'Wind offshore Missing',
                     'Wind offshore Missing Fraction',
]
result_writer = csv.DictWriter(result_file, fieldnames=result_fieldnames,
                               lineterminator='\n')
result_writer.writeheader()

for year in data_years:
    i = data_years.index(year)

    print("%d:" % (year))

    solar = float(data_solar[i])
    if (i):
        diff = solar - data_solar[i - 1]
    else:
        diff = 0

    if (year == year_solar_max):
        print("  Solar:\t%5dMWp: +%4dMWp (Before the crash)" % (solar, diff))
        solar_max = diff
    elif (solar_max > 0):
        solar_missing += solar_max - diff
        print("  Solar:\t%5dMWp: +%4dMWp: %5dMWp missing (%5.2f%%)" %
              (solar, diff, solar_missing, 100 * solar_missing / solar))
    else:
        print("  Solar:\t%5dMWp: +%4dMWp" % (solar, diff))

    onshore = float(data_onshore[i])
    if (i):
        diff = onshore - data_onshore[i - 1]
    else:
        diff = 0

    if (year == year_onshore_max):
        print("  Onshore:\t%5dMWp: +%4dMWp (Before the crash)" %
              (onshore, diff))
        onshore_max = diff
    elif (onshore_max > 0):
        onshore_missing += onshore_max - diff
        print("  Onshore:\t%5dMWp: +%4dMWp: %5dMWp missing (%5.2f%%)" %
              (onshore, diff, onshore_missing, 100 * onshore_missing / onshore))
    else:
        print("  Onshore:\t%5dMWp: +%4dMWp" % (onshore, diff))

    offshore = float(data_offshore[i])
    if (i):
        diff = offshore - data_offshore[i - 1]
    else:
        diff = 0

    if (year == year_offshore_max):
        print("  Offshore:\t%5dMWp: +%4dMWp (Before the crash)" % (offshore, diff))
        offshore_max = diff
    elif (offshore_max > 0):
        offshore_missing += offshore_max - diff
        print("  Offshore:\t%5dMWp: +%4dMWp: %5dMWp missing (%5.2f%%)" %
              (offshore, diff, offshore_missing, 100 * offshore_missing / offshore))
    else:
        print("  Offshore:\t%5dMWp: +%4dMWp" % (offshore, diff))

    result = {'Year' : year,
              'Solar Installed': solar,
              'Solar Missing': solar_missing,
              'Solar Missing Fraction': 0.0,
              'Wind onshore Installed': onshore,
              'Wind onshore Missing': onshore_missing,
              'Wind onshore Missing Fraction': 0.0,
              'Wind offshore Installed': offshore,
              'Wind offshore Missing': offshore_missing,
              'Wind offshore Missing Fraction' : 0.0}

    if (solar):
        result['Solar Missing Fraction'] = round(solar_missing / solar, 5)
    if (onshore):
        result['Wind onshore Missing Fraction'] = round(onshore_missing / onshore, 5)
    if (offshore):
        result['Wind offshore Missing Fraction'] = round(offshore_missing / offshore, 5)

    result_writer.writerow(result)
