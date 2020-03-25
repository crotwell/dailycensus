#!/usr/bin/python3
import datetime
from common import *

testing=True

loadPeople(config)
today=todayAsStr()
makeCSV(today)

with open("{}_{}_{}".format(config['unitname'], today, config['totalsTemplate']), 'r') as infile:
    summary = infile.read()
sendSummary(config, summary)
