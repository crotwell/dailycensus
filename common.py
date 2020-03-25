import csv
import datetime
import hashlib
import os
import sys
import pathlib
import re
import json
import mimetypes
from urllib.parse import urlparse
from shutil import copyfile
import calendar
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TELE = "telecommute"
LEAVE = "leave"
CAMPUS = "campus"
UNKNOWN="unknown"

STATUS_LIST = [ TELE, LEAVE, CAMPUS, UNKNOWN]

KEY_NAME= 'name'
KEY_TODAY='today'
KEY_STATUS= 'status'
KEY_EMAIL= 'email'

configFilename='config.json'
config={}

with open(configFilename, 'r') as f:
    config = json.load(f)

config['people'] = []

def loadPeople(config):
    with open(config['peopleFile'], 'r', newline='') as peoplefile:
        reader = csv.reader(peoplefile)
        for idx in range(config['peopleFileHeaders']):
            next(reader)
        for row in reader:
            config['people'].append({KEY_NAME:row[1], 'email':row[3]})
    for p in config['people']:
        print(p)

def statusLong(status):
    if status == TELE:
        return "working from home"
    elif status == LEAVE:
        return "taking some leave"
    elif status == CAMPUS:
        return "dropping by campus"
    else:
        return "Unknown status of '{}'".format(status)

def todayAsStr():
    #might be issue if system clock is utc
    now = datetime.datetime.now().replace(microsecond=0)
    today=now.date().isoformat()
    return today

def todayName():
    #might be issue if system clock is utc
    now = datetime.datetime.now()
    return calendar.day_name[now.weekday()]

def makeHash(name, today, status):
    asStr = "{name} {today} {status} {salt}".format(name=name, today=today, status=status, salt=config['salt'])
    return hashlib.sha256(asStr.encode('utf-8')).hexdigest()

def matchesHash(hash, name, today, status):
    return hash == makeHash(name, today, status)

def hashFromUrl(inUrlPath):
    return inUrlPath.split('/')[-1]

def makeFilesafeString(filename):
    keepcharacters = ('-','.','_')
    filename = re.sub(",\s\s+" , "_", filename)
    filename = re.sub("\s\s+" , "_", filename)
    return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()

def statusDirname(today):
    safeToday = makeFilesafeString(today)
    dir = "{resultsDir}/{today}".format(resultsDir=config['resultsDir'], today=safeToday)
    return dir

def statusJsonFilename(name, today):
    dir = statusDirname(today)
    statusFile = "{name}.json".format(name=name, today=today)
    statusFile = makeFilesafeString(statusFile)
    return "{dir}/{statusFile}".format(dir=dir, statusFile=statusFile)

def makeStatusAsObj(name, today, status):
    return {KEY_NAME: name, KEY_TODAY: today, KEY_STATUS:status}

def updateStatus(name, today, status):
    dir = statusDirname(today)
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
    statusFile = statusJsonFilename(name, today)
    with open(statusFile, 'w') as f:
        f.write(json.dumps(makeStatusAsObj(name, today, status)))

def makeCSV(today):
    dir = statusDirname(today)
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
    allResults = []
    totals = {TELE: 0, LEAVE: 0, CAMPUS: 0, UNKNOWN: 0}
    for dirpath, dnames, fnames in os.walk(statusDirname(today)):
        for f in fnames:
            if f.endswith(".json") and not f == "summary.json":
                with open(os.path.join(dirpath, f)) as jsonf:
                    jsonstatus = json.load(jsonf)
                    allResults.append(jsonstatus)
                    if KEY_STATUS in jsonstatus:
                        totals[jsonstatus[KEY_STATUS]] += 1
                    else:
                        print("error doing total with {}".format())
    if totals[TELE] +  totals[LEAVE] +  totals[CAMPUS] < len(config['people']):
        totals[UNKNOWN] = len(config['people']) - (totals[TELE] +  totals[LEAVE] +  totals[CAMPUS])
    summary = {KEY_TODAY: today, 'totals': totals, 'allResults': allResults}
    with open("{dir}/summary.json".format(dir=dir), 'w') as f:
        f.write(json.dumps(summary))
    with open(config['totalsTemplate'], 'r', newline='') as templatefile:
        with open("{}_{}_{}".format(config['unitname'], today, config['totalsTemplate']), 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            reader = csv.reader(templatefile)
            foundHeader = False
            for row in reader:
                if row[0] == "Date:":
                    row[1] = today
                elif row[0].startswith("Daily"):
                    pass
                elif row[0].startswith("Unit"):
                    foundHeader = True
                writer.writerows([row])
                if foundHeader:
                    row = [config['unitname'], totals[TELE], totals[LEAVE], totals[CAMPUS], totals[UNKNOWN]]
                    writer.writerows([row])
                    break

def sendEmail(person, config, htmlMessage):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "{} Daily Status for {}".format(config['unitname'], todayAsStr())
    msg['From'] = config['fromEmail']
    msg['To'] = person['email']
    htmlpart = MIMEText(htmlMessage, 'html')
    msg.attach(htmlpart)

# app specific password to bypass 2-factor auth
    #pw = "frskrrasfzxzzbrl"
    server=smtplib.SMTP(config['smtpHost'])
    #server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(config['fromEmail'],config['smtpPassword'])

    server.sendmail(config['fromEmail'], [ person['email'] ], msg.as_string())
    server.quit()


def sendSummary(config, summary):
    summMsg = """
    Summary for {unit} on {today}

    """
    with open(config['summaryTemplate'], 'r') as f:
        summMsg = f.read()
    msg = MIMEMultipart()
    msg['Subject'] = "{} Daily Status Report for {}".format(config['unitname'], todayAsStr())
    msg['From'] = config['fromEmail']
    msg['To'] = ",".join(config['resultsEmail'])
    msg.attach(MIMEText(summMsg.format(unit=config['unitname'], today=todayAsStr())))
    csvpart = MIMEText(summary, 'csv')
    fileToSend="{}_{}_{}".format(config['unitname'], todayAsStr(), config['totalsTemplate'])
    csvpart.add_header("Content-Disposition", "attachment", filename=fileToSend)
    msg.attach(csvpart)

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
