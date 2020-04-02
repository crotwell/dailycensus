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
    "form": "1455656",
    "viewkey": "0WEgw7kmLG",
    "_submit": "1",
    "password": "",
    "hidden_fields": "",
    "incomplete": "",
    "incomplete_password": "",
    "referrer": "",
    "referrer_type": "js",
    "style_version": "3",
    "viewparam": "576689",
    "field90079357": "Earth, Ocean and Environment, School of", # Academic Unit
    "field90079358" : "", # Other Academic Unit
    "field90079822" : "Thomas J. Owens",  # Unit Contact
    "field90079359-first" : "", # Other Unit Contact Name  First Name
    "field90079359-last" : "", # Other Unit Contact Name  Last Name
    "field90081290" : "owens@seis.sc.edu",  # Contact Email
    "field90079360" : "", # Other Email
    "field90083377": "Chair or Director", # Classification
    "field90080449Format": "MDY", # date-format
    "field90080449M": calendar.month_abbr[now.month], # month, Apr
    "field90080449D": "{}".format(now.day), # day 01
    "field90080449Y": "2020", # year
    "field90080322": "{}".format(jsonSummary[KEY_TOTALS][TELE]), # Telecommuting Employees
    "field90080319": "{}".format(jsonSummary[KEY_TOTALS][LEAVE]), # Employees on Leave
    "fieldCOVID": "{}".format(jsonSummary[KEY_TOTALS][COVID]), # Employees on Leave
    "field90080317": "{}".format(jsonSummary[KEY_TOTALS][CAMPUS]), # Employees Working On Campus
    "field90388556": "\n".join(jsonSummary['onCampusNames']), # Employee Names and Titles (Working on Campus)
   }

#url = "https://universityofsouthcarolina-yrckc.formstack.com/forms/index.php"
url = "http://localhost:8000/dopost"
r = requests.post(url, data=values)
with open('postformresult.html', 'w') as f:
    f.write("Status Code: {}".format(r.status_code))
    f.write(r.content.decode('ascii'))



print("{} summary:  {}, out of {}".format(today, jsonSummary['totals'], len(config['people'])))
