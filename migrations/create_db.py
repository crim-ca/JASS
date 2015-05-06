#!/usr/bin/env python
# coding:utf-8

"""
Create database in the context of a data migration.
"""

import ConfigParser
import sys
from pymongo import MongoClient
import logging

if __name__ == "__main__":
    PATH = sys.argv[1]
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(PATH)
    SETTINGS = ConfigParser.SafeConfigParser()
    SETTINGS.read(PATH)
    MC = MongoClient(SETTINGS.get("ServiceStockageAnnotations", "MongoHost"),
                     int(SETTINGS.get("ServiceStockageAnnotations",
                                      "MongoPort")))
    MC.drop_database(SETTINGS.get("ServiceStockageAnnotations", "MongoDb"))
    DB = MC[(SETTINGS.get("ServiceStockageAnnotations", "MongoDb"))]
    # Now create all the needed collections
    COLL = DB.create_collection(SETTINGS.get("ServiceStockageAnnotations",
                                             "DocumentCollection"))
    COLL = DB.create_collection(SETTINGS.get("ServiceStockageAnnotations",
                                             "SchemaCollection"))
    COLL = DB.create_collection(SETTINGS.get("ServiceStockageAnnotations",
                                             "HumanAnnotationCollection"))
    COLL.create_index("doc_id")
    MC.close()
