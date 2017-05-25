#!/usr/bin/env python
# coding:utf-8

import os
import configparser
import sys
from pymongo import MongoClient
import subprocess
import time
from pymongo.errors import ConnectionFailure


# Will also create an index if not none.
def createCollIfNotExist(db, collName, index):
    coll = None
    if db.system.namespaces.find({"name": {"$regex": "{0}.{1}".format(db, collName)}}) == 0:
        coll = db.create_collection(collName)
    else:
        coll = db[collName]
    if index != None:
        coll.create_index(index)
    return coll


def createDbIfNotExist(config_path):
    # print "Reading config from {0}".format(config_path)
    SETTINGS = configparser.ConfigParser()
    SETTINGS.read(config_path)

    retryTimes = 0
    MC = None
    while (retryTimes < 3):
        try:
            retryTimes = retryTimes + 1
            mongo_host = ""
            if "MONGO_HOST" in os.environ:
                mongo_host = os.environ["MONGO_HOST"]
            else:
                mongo_host = SETTINGS.get("ServiceStockageAnnotations", "MONGO_HOST")

            MC = MongoClient(mongo_host, int(SETTINGS.get("ServiceStockageAnnotations", "MongoPort")))

            dbName = SETTINGS.get("ServiceStockageAnnotations", "MongoDb")
            db = MC[(dbName)]
            # Now create all the needed collections

            createCollIfNotExist(db, SETTINGS.get("ServiceStockageAnnotations",
                                                  "DocumentCollection"), None)
            createCollIfNotExist(db, SETTINGS.get("ServiceStockageAnnotations",
                                                  "SchemaCollection"), "doc_id")
            createCollIfNotExist(db, SETTINGS.get("ServiceStockageAnnotations",
                                                  "HumanAnnotationCollection"), "doc_id")
            createCollIfNotExist(db, SETTINGS.get("ServiceStockageAnnotations",
                                                  "BatchAnnotationCollection"), "doc_id")
            MC.close()
            # print "MongoBD creation Successful"
            break
        except Exception as e:
            # print "Connection to mongo failed. Retrying in 10 seconds. Reason: {0}".format(str(e))
            # print "Connection to mongo failed. Retrying in 10 seconds"
            time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        createDbIfNotExist(sys.argv[1])
    else:
        createDbIfNotExist(os.environ['JASS_CONFIG_PATH'])
