import csv
import datetime
import hashlib
import os
import pathlib
import re
import json
from urllib.parse import urlparse
from shutil import copyfile
import calendar

TELE = "telecommute"
LEAVE = "leave"
CAMPUS = "campus"
UNKNOWN="unknown"

STATUS_LIST = [ TELE, LEAVE, CAMPUS, UNKNOWN]

KEY_NAME= 'name'
KEY_TODAY='today'
KEY_STATUS= 'status'
salt="adfouenlnx"
unitname="SEOE"

totalsTemplate="Daily Count.csv"


people = [
    {KEY_NAME:'Philip Crotwell', 'email':'crotwell@seis.sc.edu'},
    {KEY_NAME:'Helper2', 'email':'helper2@seis.sc.edu'}
]

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
    now = datetime.datetime.now().replace(microsecond=0)
    today=now.date().isoformat()
    return today

def todayName():
    now = datetime.datetime.now()
    return calendar.day_name[now.weekday()]

def makeHash(name, today, status):
    asStr = "{name} {today} {status} {salt}".format(name=name, today=today, status=status, salt=salt)
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
    dir = "results/{today}".format(today=safeToday)
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
    allResults = []
    totals = {TELE: 0, LEAVE: 0, CAMPUS: 0, UNKNOWN: 0}
    for dirpath, dnames, fnames in os.walk("./"):
        for f in fnames:
            if f.endswith(".json") and not f == "summary.json":
                with open(os.path.join(dirpath, f)) as jsonf:
                    jsonstatus = json.load(jsonf)
                    allResults.append(jsonstatus)
                    totals[jsonstatus[KEY_STATUS]] += 1
    if totals[TELE] +  totals[LEAVE] +  totals[CAMPUS] < len(people):
        totals[UNKNOWN] = len(people) - (totals[TELE] +  totals[LEAVE] +  totals[CAMPUS])
    summary = {KEY_TODAY: today, 'totals': totals, 'allResults': allResults}
    with open("{dir}/summary.json".format(dir=dir), 'w') as f:
        f.write(json.dumps(summary))
    with open(totalsTemplate, 'r', newline='') as templatefile:
        with open("{}_{}_{}".format(unitname, today, totalsTemplate), 'w', newline='') as outfile:
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
                    row = [unitname, totals[TELE], totals[LEAVE], totals[CAMPUS], totals[UNKNOWN]]
                    writer.writerows([row])
                    break
