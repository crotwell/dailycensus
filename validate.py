from common import *
import datetime

import os
import requests
from pprint import pprint

testing=True
now = datetime.datetime.now()

loadPeople(config)
today=todayAsStr()
fixedStatus = loadFixedStatus(config)
jsonSummary = createSummary(today)

print(json.dumps(jsonSummary, indent=2))
print()
print("{} summary:  {}, out of {}".format(today, jsonSummary['totals'], len(config['people'])))

print("seems ok...")
