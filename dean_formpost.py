from common import *
import datetime

import os
import requests
from pprint import pprint

testing=True
now = datetime.datetime.now()

loadPeople(config)
today=todayAsStr()
jsonSummary = makeCSV(today)

with open("{}_{}_{}".format(config['unitname'], today, config['totalsTemplate']), 'r') as infile:
    summary = infile.read()
#sendSummary(config, summary)

# "<form method=\"post\" accept-charset=\"UTF-8\" novalidate enctype=\"multipart/form-data\" action=\"
# https://universityofsouthcarolina-yrckc.formstack.com/forms/index.php
# \" class=\"fsForm fsSingleColumn\" id=\"fsForm3811012\">"
values = {
    "form": "3811012",
    "viewkey": "0WEgw7kmLG",
    "_submit": "1",
    "password": "",
    "hidden_fields": "",
    "incomplete": "",
    "incomplete_password": "",
    "referrer": "https://www.sc.edu/study/colleges_schools/artsandsciences/internal/for_faculty_staff/offices_depts/human_resources/covid19-census.php",
    "referrer_type": "js",
    "style_version": "3",
    "viewparam": "576689",
    "field90079357": "Earth, Ocean and Environment, School of", # Academic Unit
    "field94515295": "EWS, School of Earth, Ocean and Environment",
    "field90079358" : "Baruch Institute", # Other Academic Unit
    "field90079822-first" : "Subrahmanyam",  # Unit Contact
    "field90079822-last" : "Bulusu",  # Unit Contact
    "field90079359-first" : "Jay", # Other Unit Contact Name  First Name
    "field90079359-last" : "Pickney", # Other Unit Contact Name  Last Name
    "field90081290" : "sbulusu@geol.sc.edu",  # Contact Email
    "field90079360" : "pinckney@sc.edu", # Other Email
    "field90083377": "Chair or Director", # Classification
    "field90080449Format": "MDY", # date-format
    "field90080449M": calendar.month_abbr[now.month], # month, Apr
    "field90080449D": "{}".format(now.day), # day 01
    "field90080449Y": "2020", # year
    "field90080322": "{}".format(jsonSummary[KEY_TOTALS][TELE]), # Telecommuting Employees
    "field90588767": "{}".format(jsonSummary[KEY_TOTALS][LEAVE]), # Employees on Leave
    "field90080319": "{}".format(jsonSummary[KEY_TOTALS][COVID]), # Employees on covid Leave
    "field94514744": "{}".format(jsonSummary[KEY_TOTALS][CAMPUS]),
    "field90080317": "{}".format(jsonSummary[KEY_TOTALS][CAMPUS]), # Employees Working On Campus
    "field90388556": "\n".join(jsonSummary['onCampusNames']), # Employee Names and Titles (Working on Campus)
    "field94514210": "\n".join(jsonSummary['onCampusNames']), # Employee Names and Titles (Working on Campus)
    "field94517611": "No",
   }

#url = "https://universityofsouthcarolina-yrckc.formstack.com/forms/index.php"
url = config['resultsUrl']
r = requests.post(url, data=values)
with open('postformresult.html', 'w') as f:
    f.write("Status Code: {}".format(r.status_code))
    f.write(r.content.decode('ascii'))

# send output of form submit
msg = MIMEMultipart('alternative')
msg['Subject'] = "{} Daily Status Posting Result {}".format(config['unitname'], todayAsStr())
msg['From'] = config['fromEmail']
msg['To'] = ",".join(config['notreportingEmail'])
htmlpart = MIMEText(r.content.decode('ascii'), 'html')
msg.attach(htmlpart)
jsonpart = MIMEText(json.dumps(jsonSummary, indent=2), 'text/json')
msg.attach(jsonpart)

# app specific password to bypass 2-factor auth
#pw = "frskrrasfzxzzbrl"
server=smtplib.SMTP(config['smtpHost'])
#server.set_debuglevel(1)
server.ehlo()
server.starttls()
server.ehlo()
server.login(config['fromEmail'],config['smtpPassword'])

server.sendmail(config['fromEmail'], config['notreportingEmail'], msg.as_string())
server.quit()

sendSummaryToBoss(config, jsonSummary)
sendNotReporting(config, jsonSummary)

print("{} summary:  {}, out of {}".format(today, jsonSummary['totals'], len(config['people'])))
