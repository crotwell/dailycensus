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
from email.message import EmailMessage
from email.headerregistry import Address

TELE = "telecommute"
LEAVE = "leave"
COVID = "covidleave"
CAMPUS = "campus"
UNKNOWN="unknown"
ALL="all"

STATUS_LIST = [ TELE, LEAVE, COVID, CAMPUS, UNKNOWN]

KEY_NAME= 'name'
KEY_LOC= 'loc'
KEY_TODAY='today'
KEY_STATUS= 'status'
KEY_EMAIL= 'email'
KEY_FIXED = 'fixed'
KEY_TOTALS = 'totals'

configFilename='config.json'
config={}

with open(configFilename, 'r') as f:
    config = json.load(f)

config['people'] = []

def loadPeople(config):
    if config['peopleFile'].endswith('.csv'):
        nameCol = config['peopleFileNameCol']
        emailCol = config['peopleFileEmailCol']
        locCol = config['peopleFileLocCol']
        with open(config['peopleFile'], 'r', newline='') as peoplefile:
            reader = csv.reader(peoplefile)
            for idx in range(config['peopleFileHeaders']):
                next(reader)
            for row in reader:
                personName = reverseName(row[nameCol])
                config['people'].append({KEY_NAME:personName, 'email':row[emailCol], KEY_LOC:row[locCol]})
    elif config['peopleFile'].endswith('.json'):
        config['people'] = json.load(config['peopleFile'])

def reverseName(name):
    if "," in name:
        name = " ".join(name.split(",")[::-1])
    return name.strip()

def loadScreeningReminder(config):
    htmlMsg=""
    try:
        with open(config['screeningReminderFile'], 'r') as f:
            htmlMsg = f.read()
            config['screeningReminder'] = htmlMsg
            return htmlMsg
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

def loadFixedStatus(config):
    with open(config['fixedStatusFile']) as f:
        fixed = json.load(f)
        for f in fixed:
            f['name'] = reverseName(f['name'])
        return fixed

def statusLong(status):
    if status == TELE:
        return "working from home"
    elif status == LEAVE:
        return "taking some leave"
    elif status == COVID:
        return "taking some leave due to COVID-19"
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

def makeStatusAsObj(name, today, status, loc):
    return {KEY_NAME: name, KEY_TODAY: today, KEY_STATUS:status, KEY_LOC: loc}

def updateStatus(name, today, status, loc):
    dir = statusDirname(today)
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
    statusFile = statusJsonFilename(name, today)
    with open(statusFile, 'w') as f:
        f.write(json.dumps(makeStatusAsObj(name, today, status, loc)))

def createSummary(today):
    dir = statusDirname(today)
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
    allResults = []
    totals = {TELE: 0, LEAVE: 0, COVID: 0, CAMPUS: 0, UNKNOWN: 0, ALL: len(config['people'])}
    fixedStatus = loadFixedStatus(config)
    for dirpath, dnames, fnames in os.walk(statusDirname(today)):
        for f in fnames:
            if f.endswith(".json") and not f == "summary.json":
                with open(os.path.join(dirpath, f)) as jsonf:
                    jsonstatus = json.load(jsonf)
                    if not KEY_LOC in jsonstatus:
                        for p in config['people']:
                            if p[KEY_NAME] == jsonstatus[KEY_NAME]:
                                jsonstatus[KEY_LOC] = p[KEY_LOC]
                            else:
                                jsonstatus[KEY_LOC] = "Unknown"
                    allResults.append(jsonstatus)
                    if KEY_STATUS in jsonstatus:
                        totals[jsonstatus[KEY_STATUS]] += 1
                    else:
                        print("error doing total with {}".format(jsonstatus))
    totalNum = len(config['people'])
    for jsonstatus in fixedStatus:
        jsonstatus[KEY_TODAY] = today
        jsonstatus[KEY_FIXED] = True

        if not KEY_LOC in jsonstatus:
            for p in config['people']:
                if p[KEY_NAME] == jsonstatus[KEY_NAME]:
                    jsonstatus[KEY_LOC] = p[KEY_LOC]
        found = False
        for r in allResults:
            if jsonstatus[KEY_NAME] == r[KEY_NAME]:
                # reported so don't overwrite
                found = True
                break
        if not found:
            allResults.append(jsonstatus)
            totalNum += 1
            if KEY_STATUS in jsonstatus:
                totals[jsonstatus[KEY_STATUS]] += 1
            else:
                print("error fixed status for {}".format(jsonstatus))
    totals[ALL] = totalNum

    if totals[TELE] +  totals[LEAVE] +  totals[COVID] +  totals[CAMPUS] < totalNum:
        totals[UNKNOWN] = totalNum - (totals[TELE] +  totals[LEAVE]  +  totals[COVID] +  totals[CAMPUS])

    didNotReport = []
    for p in config['people']:
        found = False
        for r in allResults:
            if r[KEY_NAME] == p[KEY_NAME]:
                found = True
                break
        if not found:
            didNotReport.append(p)


    onCampusNames = []
    for p in allResults:
        if p[KEY_STATUS] == CAMPUS:
            onCampusNames.append(f"{p[KEY_NAME]}, {p[KEY_LOC]}")


    summary = {KEY_TODAY: today, KEY_TOTALS: totals, 'onCampusNames': onCampusNames, 'allResults': allResults, 'notReporting': didNotReport, 'fixedStatus': fixedStatus}
    return summary


def checkValidEmailAddr(email):
    EMAIL_REGEX = re.compile(r"^\S+@\S+\.\S+$")
    if not EMAIL_REGEX.match(email):
        raise Exception(f"{email} doesn't look like an email address")
    a = Address(email)


def sendEmail(person, config, htmlMessage):
    checkValidEmailAddr(config['fromEmail'])
    checkValidEmailAddr(person['email'])
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

def sendSimpleEmail(emailToList, config, textMessage, subject):
        checkValidEmailAddr(config['fromEmail'])
        toList = []
        for e in emailToList:
            checkValidEmailAddr(e)
            toList.append(Address(e))
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = Address(config['fromEmail'])
        msg['To'] = ', '.join(emailToList)
        msg.set_content(textMessage)

    # app specific password to bypass 2-factor auth
        #pw = "frskrrasfzxzzbrl"
        server=smtplib.SMTP(config['smtpHost'])
        #server.set_debuglevel(1)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(config['fromEmail'],config['smtpPassword'])

        server.sendmail(config['fromEmail'], emailToList, msg.as_string())
        server.quit()

def sendSummaryToBoss(config, jsonSummary):
    checkValidEmailAddr(config['fromEmail'])
    for e in config['resultsEmail']:
        checkValidEmailAddr(e)
    onCampusNames="\n    ".join(jsonSummary['onCampusNames'])
    tele=jsonSummary[KEY_TOTALS][TELE]
    leave=jsonSummary[KEY_TOTALS][LEAVE]
    covid=jsonSummary[KEY_TOTALS][COVID]
    campus=jsonSummary[KEY_TOTALS][CAMPUS]
    numpeople=len(config['people'])
    subject="{} Daily Status Summary for {}".format(config['unitname'], todayAsStr())
    textMessage = f"""
    {todayAsStr()}
    {tele} # Telecommuting Employees
    {leave} # Employees on Leave
    {covid} # Employees on covid Leave
    {campus} # Employees Working On Campus
    {numpeople} # Total employees in list

    # Employee Names and Locations (Working on Campus)
    {onCampusNames}
    """
    sendSimpleEmail(config['resultsEmail'], config, textMessage, subject)


def sendNotReporting(config, jsonSummary):
    checkValidEmailAddr(config['fromEmail'])
    for e in config['notreportingEmail']:
        checkValidEmailAddr(e)
    onCampusNames="\n    ".join(jsonSummary['onCampusNames'])
    noReportList = []
    for n in jsonSummary['notReporting']:
        noReportList.append(f"{n['name']}, {n['email']}, {n['loc']}")
    noReportNames="\n    ".join(noReportList)

    tele=jsonSummary[KEY_TOTALS][TELE]
    leave=jsonSummary[KEY_TOTALS][LEAVE]
    covid=jsonSummary[KEY_TOTALS][COVID]
    campus=jsonSummary[KEY_TOTALS][CAMPUS]
    numpeople=len(config['people'])
    numNoReport=len(noReportList)
    subject="{} Daily Status Not Reporting for {}".format(config['unitname'], todayAsStr())
    textMessage = f"""
    {todayAsStr()}
    {tele} # Telecommuting Employees
    {leave} # Employees on Leave
    {covid} # Employees on covid Leave
    {campus} # Employees Working On Campus
    {numNoReport} # Employees Not Reporting
    {numpeople} # Total employees in list

    # Employee Names and Locations (Working on Campus)
    {onCampusNames}

    # Employee Names Not Reporting:
    {noReportNames}
    """
    sendSimpleEmail(config['notreportingEmail'], config, textMessage, subject)


def sendSummary(config, summary):
    checkValidEmailAddr(config['fromEmail'])
    for e in config['resultsEmail']:
        checkValidEmailAddr(e)
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
