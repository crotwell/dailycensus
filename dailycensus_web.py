#!/usr/bin/python3
import datetime
import sys
from common import *
import traceback

testing=True

errorHtml="""
<html>
    <body>
        <h3>Error Reporting Status {today}</h3>
        <p>We didn't understand that?</p>
        <p>It is possible you clicked a link from an older email. The links expire each day.</p>
        <h3>{path}</h3>
    </body>
</html>
"""

defaultResponseMsg = """
<html>
    <body>
        <h1>DEFAULT TEMPLATE</h1>
        <h3>{name}</h3>
        <h3>{status}</h3>
        <h3>{today}</h3>
    </body>
</html>
"""

htmlResponse=defaultResponseMsg
try:
    with open(config['htmlTemplate'], 'r') as f:
        htmlResponse = f.read()

except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
    #htmlResponse=defaultResponseMsg

def app(environ, start_response):
    try:
        if environ['PATH_INFO'].endswith('postformresult.html'):
            with open('postformresult.html', 'r') as f:
                postresponse = f.read()
                postresponse = postresponse.encode('utf-8')
                start_response("200 OK", [
                    ("Content-Type", "text/html"),
                    ("Content-Length", str(len(postresponse)))
                ])
                return iter([postresponse])
        elif environ['PATH_INFO'].endswith('favicon.ico'):
            data = "nope"
            print("flavicon: "+data)
            data = data.encode('utf-8')
            start_response("404", [
                ("Content-Type", "text/html"),
                ("Content-Length", str(len(data)))
            ])
            return iter([data])
        else:
            return doSubmitOk(environ, start_response)
    except:
        tb = traceback.format_exc()
        print(tb)
        raise

def doSubmitOk(environ, start_response):
    name="Jane Doe"
    now = datetime.datetime.now().replace(microsecond=0)
    today=now.date().isoformat()
    status=UNKNOWN
    screeningReminder=""
    path = environ.get('PATH_INFO', '')
    hash = hashFromUrl(path)
    data=None
    loadPeople(config)
    for s in STATUS_LIST:
        print(s)
    for u in config['people']:
        for s in STATUS_LIST:
            if matchesHash(hash, u[KEY_NAME], today, s):
                name=u[KEY_NAME]
                status=s
                updateStatus(name, today, status, u[KEY_LOC])
                if status == CAMPUS:
                    loadScreeningReminder()
                    screeningReminder=loadScreeningReminder()
                data = htmlResponse.format(name=name,
                    today=today,
                    status=status,
                    statuslong=statusLong(status),
                    loc=u[KEY_LOC],
                    screeningReminder=screeningReminder).encode('utf-8')
                break
        else:
            # Continue if the inner loop wasn't broken.
            continue
        # Inner loop was broken, break the outer.
        break
    if data is not None:
        start_response("200 OK", [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(data)))
        ])
        return iter([data])
    else:
        data = errorHtml.format(path=path,today=today)
        print(data)
        data = data.encode('utf-8')
        start_response("404", [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(data)))
        ])
        return iter([data])
