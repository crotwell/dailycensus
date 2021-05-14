#!/usr/bin/python3
import datetime
import sys
import traceback
from time import sleep
from common import *

testing=False

today=todayAsStr()
baseurl=config['baseurl']
if testing:
    baseurl="http://localhost:8000/dailycensus/"

defaultMsg="""

<html>
  <head></head>
  <body>
      <h1>DEFAULT TEMPLATE</h1>
    <h3>Please report your work status for today {today}.</h3>
    <ul>
      <li><a href="{baseurl}{medtele}">Working remotely due to medical condition/dependent care</a></li>
      <li><a href="{baseurl}{quartele}">Working remotely due to isolation/quarantine</a></li>
      <li><a href="{baseurl}{tele}">Telecommuting: Other reason ((for situations unrelated to Covid-19; Faculty working remotely)</a></li>
      <li><a href="{baseurl}{leave}">On Leave</a></li>
      <li><a href="{baseurl}{campus}">Physically Reporting to Work</a></li>
    </ul>
    <p>Thank you</p>
  </body>
</html>
"""


htmlMsg=defaultMsg
try:
    with open(config['emailTemplate'], 'r') as f:
        htmlMsg = f.read()
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
    #htmlMsg=defaultMsg

loadPeople(config)
fixedStatus = loadFixedStatus(config)

num_sent=0
print(htmlMsg)
for person in config['people']:
    found = False
    for f in fixedStatus:
        if person[KEY_NAME] == f[KEY_NAME]:
            # fixed status, skip email
            found = True
            break
    if found:
        # fixed status, skip email
        continue

    print(person)
    htmlMessage = htmlMsg.format(name=person[KEY_NAME],
        todayname=todayName(),
        today=today,
        baseurl=baseurl,
        ninemo=makeHash(person[KEY_NAME], today, NINEMO),
        medtele=makeHash(person[KEY_NAME], today, MEDTELE),
        quartele=makeHash(person[KEY_NAME], today, QUARTELE),
        tele=makeHash(person[KEY_NAME], today, TELE),
        campus=makeHash(person[KEY_NAME], today, CAMPUS),
        covid=makeHash(person[KEY_NAME], today, COVID),
        leave=makeHash(person[KEY_NAME], today, LEAVE))
    try:
        sendEmail(person, config, htmlMessage)
        num_sent += 1
        sleep(5)
    except Exception:
        traceback.print_exc()
        sleep(10)
        print("try again..., fail hard if this one crashes too")
        sendEmail(person, config, htmlMessage)
print("{} sent {} out of {}".format(today, num_sent, len(config['people'])))
