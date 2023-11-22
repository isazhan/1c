import json
from pymongo import MongoClient

db = json.load(open('dbconfig.json'))['default']
host = db['CLIENT']['host']
name = db['NAME']

def get_db_handle():

    client = MongoClient(host)
    db_handle = client[name]

    return db_handle