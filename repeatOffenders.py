from common import *
import datetime
import time

import os
import requests
from pprint import pprint


loadPeople(config)
today=todayAsStr()
fixedStatus = loadFixedStatus(config)

oneday = datetime.timedelta(days=1)
numdays = 0
maxMiss = 2
now = datetime.datetime.now().replace(microsecond=0)
theday = now
missedReport = {}
for p in config['people']:
    p['missedReport'] = 0
for d in range(0,7):
    if theday.weekday() < 5:
        # Sat=5 Sun=6
        numdays += 1
        dayStr=theday.date().isoformat()
        summary = createSummary(dayStr)
        for mrp in summary['notReporting']:
            for p in config['people']:
                if p['name'] == mrp['name']:
                    p['missedReport'] += 1
                    break
    theday=theday - oneday

sortedPeople = sorted(config['people'], key=lambda p: p['missedReport'])
print(f'SEOE Missed more than {maxMiss} reports in last {numdays}')
for p in sortedPeople:
    if p['missedReport'] > maxMiss and p['loc'] == 'SEOE':
        print(f"Missed:  {p['missedReport']}/{numdays} {p['name']} {p['email']} {p['loc']}")

print("")
print(f'Baruch Missed more than {maxMiss} reports in last {numdays} workdays')
for p in sortedPeople:
    if p['missedReport'] > maxMiss and p['loc'] != 'SEOE':
        print(f"Missed:  {p['missedReport']}/{numdays} {p['name']} {p['email']} {p['loc']}")
