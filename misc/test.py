from pymongo import MongoClient
import pymongo
import os
import datetime

cluster = MongoClient("mongodb://127.0.0.1:27017")
mongo_db = cluster["vvz"]

sem = mongo_db["semester"]
gebaeude = mongo_db["gebaeude"]
raum = mongo_db["raum"]
cod = mongo_db["code"]
rub = mongo_db["rubrik"]
mod = mongo_db["modul"]
per = mongo_db["person"]
stu = mongo_db["studiengang"]
anf = mongo_db["anforderung"]
anfkat = mongo_db["anforderungkategorie"]
ver = mongo_db["veranstaltung"]

s = sem.find_one({"kurzname": "2024WS"})
v = ver.find_one({"semester": s["_id"], "name_de": "Analysis III"})
print(v["name_de"])

r = raum.find_one({"_id": v["einmaliger_termin"][0]["raum"][0]})
print(r["name_de"])

ver.update_many({"_id": v["_id"], "einmaliger_termin.raum": { "$elemMatch": { "$eq": r["_id"] }}}, { "$pull": {"einmaliger_termin.$.raum" : r["_id"]}})
print("danach")
print(v["einmaliger_termin"])
