
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
import cgitb
cgitb.enable()

import json

class StoreHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print("do_POST")
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST'})
        print(form)
        for x in form:
            print("{} -> '{}'".format(x, form[x].value))

        self.respond("uploaded , thanks")

    def do_GET(self):
        response = """
        <html><body>
        <form method="post" enctype="multipart/form-data" action="/dopost">
        <input type="hidden" name="form" value="3811012" />
        <input type="text" name="field90079822" value=""/>
        <div>
    <label for="say">What greeting do you want to say?</label>
    <input name="say" id="say" value="Hi">
  </div>
  <div>
    <label for="to">Who do you want to say it to?</label>
    <input name="to" id="to" value="Mom">
  </div>
        <p>File: <input type="number" name="num"></p>
        <p><input type="submit" value="Upload"></p>
        </form>
        </body></html>
        """

        self.respond(response)

    def respond(self, response, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", len(response))
        self.end_headers()
        self.wfile.write(response.encode('ascii'))

def run(server_class=HTTPServer, handler_class=StoreHandler):
    server_address = ('', 8888)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

run()
