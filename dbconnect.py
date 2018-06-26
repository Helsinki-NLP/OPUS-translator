import pymysql.cursors

with open("/home/cloud-user/secrets/user") as f:
    user = f.read()[:-1]

with open("/home/cloud-user/secrets/password") as f:
    password = f.read()[:-1]

with open("/home/cloud-user/secrets/database") as f:
    db = f.read()[:-1]

def connection():
    conn = pymysql.connect(host='localhost',
                           user=user,
                           password=password,
                           db=db,
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

    c = conn.cursor()

    return c, conn
