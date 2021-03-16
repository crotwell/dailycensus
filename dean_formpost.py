from common import *
import datetime
import time

import os
import requests
from pprint import pprint


testing=True
now = datetime.datetime.now()

loadPeople(config)
today=todayAsStr()
jsonSummary = createSummary(today)


statusDir = statusDirname(today)
with open("{dir}/summary.json".format(dir=statusDir), 'w') as f:
    f.write(json.dumps(jsonSummary, indent=2))


try:
    sendSummaryToBoss(config, jsonSummary)
except Exception:
    # try again
    logging.exception("Exception trying to sendSummaryToBoss, retry...")
    time.sleep(3)
    sendSummaryToBoss(config, jsonSummary)
try:
    sendNotReporting(config, jsonSummary)
except Exception:
    # try again???
    logging.exception("Exception trying to sendNotReporting, retry...")
    time.sleep(3)
    sendNotReporting(config, jsonSummary)

print("{} summary:  {}, out of {}".format(today, jsonSummary['totals'], len(config['people'])))
