import pymysql.cursors
import os

user = os.environ["DBUSER"]
password = os.environ["DBPASSWORD"]
db = os.environ["DBNAME"]

def connection():
    conn = pymysql.connect(host='localhost',
                           user=user,
                           password=password,
                           db=db,
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

    c = conn.cursor()

    return c, conn
