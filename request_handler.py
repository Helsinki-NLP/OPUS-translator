import requests
import html
import os

class RequestHandler:

    def __init__(self):
        self.s = requests.Session()
        self.s.cert = (
            os.environ["BACKENDCERT"],
            os.environ["BACKENDKEY"]
        )
        self.s.verify = os.environ["BACKENDCA"]
        self.root_url = os.environ["BACKENDURL"]

    def get(self, url, params):
        r = self.s.get(self.root_url+url, params=params)
        return html.unescape(r.text)

    def put(self, url, params):
        r = self.s.put(self.root_url+url, params=params)
        return r.text

    def post(self, url, params):
        r = self.s.post(self.root_url+url, params=params)
        return r.text

    def upload(self, url, params, filename):
        with open(filename, "rb") as f:
            r = self.s.put(self.root_url+url, params=params, data=f)
        return r.text

    def delete(self, url, params):
        r = self.s.delete(self.root_url+url, params=params)
        return r.text

