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
    "field90079358" : "", # Other Academic Unit
    "field90079822" : "Thomas J. Owens",  # Unit Contact
    "field90079359-first" : "Jae", # Other Unit Contact Name  First Name
    "field90079359-last" : "Choe", # Other Unit Contact Name  Last Name
    "field90081290" : "owens@seis.sc.edu",  # Contact Email
    "field90079360" : "jchoe@geol.sc.edu ", # Other Email
    "field90083377": "Chair or Director", # Classification
    "field90080449Format": "MDY", # date-format
    "field90080449M": calendar.month_abbr[now.month], # month, Apr
    "field90080449D": "{}".format(now.day), # day 01
    "field90080449Y": "2020", # year
    "field90080322": "{}".format(jsonSummary[KEY_TOTALS][TELE]), # Telecommuting Employees
    "field90588767": "{}".format(jsonSummary[KEY_TOTALS][LEAVE]), # Employees on Leave
    "field90080319": "{}".format(jsonSummary[KEY_TOTALS][COVID]), # Employees on covid Leave
    "field90080317": "{}".format(jsonSummary[KEY_TOTALS][CAMPUS]), # Employees Working On Campus
    "field90388556": "\n".join(jsonSummary['onCampusNames']), # Employee Names and Titles (Working on Campus)
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
msg['To'] = ",".join(config['resultsEmail'])
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

server.sendmail(config['fromEmail'], config['resultsEmail'], msg.as_string())
server.quit()

#kristaEmail='KRUSSELL@sc.edu'
kristaEmail='crotwell@seis.sc.edu'
onCampusNames="\n".join(jsonSummary['onCampusNames'])
tele=jsonSummary[KEY_TOTALS][TELE]
leave=jsonSummary[KEY_TOTALS][LEAVE]
covid=jsonSummary[KEY_TOTALS][COVID]
campus=jsonSummary[KEY_TOTALS][CAMPUS]
numpeople=len(config['people'])
subject="{} Daily Status Summary for {}".format(config['unitname'], todayAsStr())
message = f"""
{todayAsStr()}
{tele} # Telecommuting Employees
{leave} # Employees on Leave
{covid} # Employees on covid Leave
{campus} # Employees Working On Campus
{numpeople} # Total employees in list

# Employee Names and Titles (Working on Campus)
{onCampusNames}
"""
sendSimpleEmail(kristaEmail, config, message, subject)

print("{} summary:  {}, out of {}".format(today, jsonSummary['totals'], len(config['people'])))
