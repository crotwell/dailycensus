#!/usr/bin/python3
import datetime
import sys
from common import *

testing=True

errorHtml="""
<html>
    <body>
        <h3>Error Reporting Status</h3>
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
    name="Jane Doe"
    now = datetime.datetime.now().replace(microsecond=0)
    today=now.date().isoformat()
    status=UNKNOWN
    path = environ.get('PATH_INFO', '')
    hash = hashFromUrl(path)
    data=None
    for u in config['people']:
        for s in STATUS_LIST:
            if matchesHash(hash, u[KEY_NAME], today, s):
                name=u[KEY_NAME]
                status=s
                updateStatus(name, today, status)
                data = htmlResponse.format(name=name,
                    today=today,
                    status=status,
                    statuslong=statusLong(status)).encode('utf-8')
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
        data = errorHtml.format(path=path,today=today).encode('utf-8')
        start_response("404", [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(data)))
        ])
        return iter([data])
