#!/usr/bin/python3
import datetime
import sys
from common import *

testing=False

today=todayAsStr()
baseurl="http://dailycensus.geol.sc.edu/dailycensus/"
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
    with open('email_template.html', 'r') as f:
        htmlMsg = f.read()
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
    #htmlMsg=defaultMsg

print(htmlMsg)
for u in people:
    print(u)
    print("{name} {todayname} {today} {baseurl} {tele} {campus} {leave}".format(name=u[KEY_NAME],
        todayname=todayName(),
        today=today,
        baseurl=baseurl,
        tele=makeHash(u[KEY_NAME], today, TELE),
        campus=makeHash(u[KEY_NAME], today, CAMPUS),
        leave=makeHash(u[KEY_NAME], today, LEAVE)))
    htmlMessage = htmlMsg.format(name=u[KEY_NAME],
        todayname=todayName(),
        today=today,
        baseurl=baseurl,
        tele=makeHash(u[KEY_NAME], today, TELE),
        campus=makeHash(u[KEY_NAME], today, CAMPUS),
        leave=makeHash(u[KEY_NAME], today, LEAVE))
    print(htmlMessage+"\n\n\n")
    sendEmail(u, htmlMessage)
