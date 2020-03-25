#!/usr/bin/python3
import datetime
import sys
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
      <li><a href="{baseurl}{tele}">Telecommuting</a></li>
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

print(htmlMsg)
for person in config['people']:
    print(person)
    htmlMessage = htmlMsg.format(name=person[KEY_NAME],
        todayname=todayName(),
        today=today,
        baseurl=baseurl,
        tele=makeHash(person[KEY_NAME], today, TELE),
        campus=makeHash(person[KEY_NAME], today, CAMPUS),
        leave=makeHash(person[KEY_NAME], today, LEAVE))
    sendEmail(person, config, htmlMessage)
    sleep(5)
