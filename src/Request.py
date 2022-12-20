import requests


def make_request(msg, rq_type, ):
    try:
        x = exec(msg)
        if x.status_code == 200:
            return x.text
    except Exception as e:
        return e

msg = requests.get('https://w3schools.com/python/demopage.htm')
print(make_request(msg))

class myHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.redirect()
    def do_POST(self):
        self.redirect()
    def redirect(self):
        self.send_response(307)
        self.send_header('Location','http://www.example.com')
        self.end_headers()