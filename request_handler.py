import requests

class RequestHandler:

    def __init__(self):
        self.s = requests.Session()
        self.s.cert = (
            "/var/www/cert/vm1637.kaj.pouta.csc.fi/user/certificates/developers@localhost.crt",
            "/var/www/cert/vm1637.kaj.pouta.csc.fi/user/keys/developers@localhost.key"
        )
        self.s.verify = "/var/www/cert/vm1637.kaj.pouta.csc.fi/ca.crt"
        self.root_url = "https://vm1637.kaj.pouta.csc.fi:443/ws"

    def get(self, url, params):
        r = self.s.get(self.root_url+url, params=params)
        return r.text

    def put(self, url, params):
        r = self.s.put(self.root_url+url, params=params)
        return r.text

    def post(self, url, params):
        r = self.s.post(self.root_url+url, params=params)
        return r.text

    def upload(self, url, params, filename):
        with open(filename, "rb") as f:
            r = self.s.post(self.root_url+url, params=params, data=f)
        return r.text

    def delete(self, url, params):
        r = self.s.delete(self.root_url+url, params=params)
        return r.text

'''
rh = RequestHandler()

print(rh.upload(
    "/storage/corpustest2/mikkotest/uploads/html/fi/2.html",
    {"uid": "mikkotest", "action": "import"},
    "2.html"
    )
)
'''
