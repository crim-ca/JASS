#!/usr/bin/env python
# coding:utf-8

from jass.storage_exception import *
from bson.errors import *
from jass.storage_manager import StorageManager
# Mongo some interesting performance statistics
# http://blog.mongolab.com/2014/01/how-big-is-your-mongodb/


class DocumentManager(StorageManager):
    def deleteDocumentWithContents(self, documentId):
        """
        Delete document and all related annotations
        """
        pass
