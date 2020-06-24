#!/usr/bin/python3
import datetime
from common import *

testing=True

loadPeople(config)
today=todayAsStr()
jsonSummary = createSummary(today)

statusDir = statusDirname(today)
with open("{dir}/summary.json".format(dir=statusDir), 'w') as f:
    f.write(json.dumps(jsonSummary, indent=2))



print("{} summary:  {}, out of {}".format(today, jsonSummary['totals'], len(config['people'])))
