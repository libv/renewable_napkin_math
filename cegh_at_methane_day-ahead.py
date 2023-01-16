#!/usr/bin/python3
#
# DO NOT RUN THIS.
#
# ... Unless you absolutely need to.
# It floods your working dir with 2000+ little html files, and it slightly
# hammers the good people at cegh.at
#
#

import sys
from bs4 import BeautifulSoup
import re
import datetime
from pathlib import Path
import subprocess
import csv

csv_filename = "cegh_at_methane_day-ahead.csv"
cegh_table = []

date_delta = datetime.timedelta(days=1)
date_start = datetime.date.fromisoformat("2016-12-01")
date_stop = datetime.date.fromisoformat("2023-01-01")

def date_from_weekday(date, weekday):
    day_list = ["Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
                "Weekend" ]
    if (not weekday in day_list):
        print("Unknown day: %s" % weekday)
        return None

    if (weekday == "Weekend"):
        weekday = "Saturday"

    while True:
        day = date.strftime('%A')

        if (day == weekday):
            return date

        date += date_delta

def data_table_add_html(html):
    global cegh_table
    table = []

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text()

    #strip suffix
    text = re.sub("[\n]*[ ]*VWAP \.\.\..*\n  \n\n", "", text, 0, re.M)
    entries = re.split("\n\n\n", text)[3:]

    for line in entries:
        row = re.split("\n", line)

        if (row[8] == "-" or
            row[7] == "-"):
            continue

        contract_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
        delivery_date = date_from_weekday(contract_date, row[1])

        if (delivery_date == None):
            continue

        data = (delivery_date, float(row[8]))
        table.append(data)
        #print(data)

        if (row[1] == "Weekend"): #add sunday as well
            delivery_date += date_delta

            data = (delivery_date, float(row[8]))
            table.append(data)
            #print(data)

    table.sort(key=lambda t: t[0].isoformat())

    #print(table)

    # fixup holes.
    if len(table) > 1:
        new = []
        last = None

        for t in table:
            if (last != None):
                date = last[0]
                while True:
                    date += date_delta
                    if (date == t[0]):
                        break
                    new.append((date, last[1]))

            new.append(t)
            last = t
        table = new

    # add, and filter out days already there.
    if (len(cegh_table) < 1):
        cegh_table.extend(table)
    else:
        date_last = cegh_table[-1][0]

        for t in table:
            if (t[0] > date_last):
                cegh_table.append(t)



def html_file_parse(filename):
    html_file = open(html_filename, 'r')

    html = html_file.read()

    data_table_add_html(html)

    html_file.close()

trading_date = date_start
while True:
    #print("Contract date %s: %s" % (trading_date.strftime("%Y%m%d"),
    #                           trading_date.strftime('%A')))

    html_filename = "cegh_" + trading_date.strftime("%Y%m%d") + ".html"
    html_file = Path(html_filename)

    if not html_file.is_file():
        print("File %s not found." % (html_file))
        command = "wget \"https://www.cegh.at/umbraco/surface/MarketDataSurface/GetDayAheadSingleDay?lngIsoCode=en-US&marketId=0&stringDate=\""
        command += trading_date.strftime("%Y%m%d")
        command += " -O " + html_filename
        print ("\t%s" % command)
        subprocess.Popen(command, shell=True).wait()

    html_file_parse(html_filename)

    trading_date += date_delta
    if (trading_date == date_stop):
        break

csv_table = []

for t in cegh_table:
    csv_table.append({"Delivery Date" : t[0].isoformat(),
                      "Weighted Average Price EUR/MWh" : t[1]})

fieldnames = ['Delivery Date', 'Weighted Average Price EUR/MWh']

with open(csv_filename, mode='w') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames,
                                lineterminator='\n')

    csv_writer.writeheader()
    csv_writer.writerows(csv_table)
