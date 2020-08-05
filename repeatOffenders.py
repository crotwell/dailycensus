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

now = datetime.datetime.now().replace(microsecond=0)
theday = now
missedReport = {}
for p in config['people']:
    p['missedReport'] = 0
for d in range(0,7):
    if theday.weekday() < 5:
        # Sat=5 Sun=6
        dayStr=theday.date().isoformat()
        summary = createSummary(dayStr)
        for mrp in summary['notReporting']:
            for p in config['people']:
                if p['name'] == mrp['name']:
                    p['missedReport'] += 1
                    break
    theday=theday - oneday


for p in config['people']:
    print(f"Missed: {p['name']} {p['missedReport']}")
