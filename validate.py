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

allIsOk = True

# check known work locations
knownLocs = [ 'SEOE', 'Baruch - Coast', 'Baruch - Campus']

today=todayAsStr()
fixedStatus = loadFixedStatus(config)
jsonSummary = createSummary(today)

for p in config['people']:
    if not p[KEY_LOC] in knownLocs:
        allIsOk = False
        print(f"Unknown loc for {json.dumps(p)}")
    try:
        checkValidEmailAddr(p['email'])
    except:
        allIsOk = False
        print(f'Missing email for {p["name"]}')


allFound = True
for f in fixedStatus:
    found = False
    for p in config['people']:
        if p['name'] == f['name']:
            found = True
            break
    if not found:
        allIsOk = False
        allFound = False
        print(f'Unable to find {f["name"]} from fixedStatus')
if allFound:
    print(f"Found all {len(fixedStatus)} fixedStatus in people")

print("{} summary:  {}, out of {}".format(today, jsonSummary['totals'], len(config['people'])))

if allIsOk:
    print("seems ok...remember to restart gunicorn if needed")
else:
    print("\n\nLooks like there are problems!")
