#!/usr/bin/env python
# coding:utf-8

"""
Various utilities for mongoDB usage.
"""

from bson.objectid import ObjectId


def changeDocIdToString(mongoDoc):
    """
    Changes the _id to string.
    Will crash if mongoDoc is not a valid Mongo Document
    """
    if(mongoDoc is not None):
        mongoDoc['_id'] = str(mongoDoc['_id'])


def changeDocIdToMongoId(jsonDoc):
    """
    Changes the _id to ObjectId.
    Will crash if jsonDoc is not a simple JSON object with _id field
    """
    if(jsonDoc is not None):
        jsonDoc['_id'] = ObjectId(jsonDoc['_id'])


def isObjectId(strId):
    return ObjectId.is_valid(strId)
