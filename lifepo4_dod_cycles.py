#!/usr/bin/python

#
# https://www.powertechsystems.eu/home/tech-corner/lithium-iron-phosphate-lifepo4/
# has a chart which estimates the number of cycles a lifepo4 battery has compared
# to depth of discharge.
#
# We assume that .25C is a good enough metric for grid level storage.
#
# This program pours 5% increments into a dictionary. The values were
# manually guesstimated.
#

import sys
import csv

if (len(sys.argv) != 2):
    print("Error: Wrong number of arguments.")
    print("%s <output csv>" % (sys.argv[0]))
    sys.exit()

filename_output = sys.argv[1]

# After 6000.0 100% cycles the battery will have degraded to 80% original capacity.
cycles = [{100:   6000.0,
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
           5:  1000000.0}] # guess, no more data


fieldnames = [100,
              95,
              90,
              85,
              80,
              75,
              70,
              65,
              60,
              55,
              50,
              45,
              40,
              35,
              30,
              25,
              20,
              15,
              10,
              5,]

print("Writing cycle data to %s" % filename_output)

with open(filename_output, mode='w') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames,
                                lineterminator='\n')

    csv_writer.writeheader()
    csv_writer.writerows(cycles)
