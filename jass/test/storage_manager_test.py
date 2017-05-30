import unittest
import logging
import random
import os
import json
from pymongo import MongoClient

from jass.storage_manager import StorageManager
from jass import settings
from jass.storage_exception import *


# other useful tools.

class TestStorageManager(unittest.TestCase):
    d = None

    def setUp(self):
        settings.Settings.Instance().LoadConfig(
            os.path.join(os.path.dirname(__file__), "..", "..", "configs", "test", "config.ini"))

        host = settings.GetConfigValue("ServiceStockageAnnotations", "MONGO_HOST")
        port = int(settings.GetConfigValue("ServiceStockageAnnotations", "MongoPort"))
        c = MongoClient(host, port, connect=False)
        c.admin.command("ismaster")
        dbname = settings.GetConfigValue("ServiceStockageAnnotations", "MongoDb")

        # Force connection test
        # https://api.mongodb.com/python/current/migrate-to-pymongo3.html#mongoclient-connects-asynchronously
        c.admin.command("ismaster")

        c.drop_database(dbname)
        c.close()
        self.d = StorageManager()
        self.d.setCollection(settings.GetConfigValue("ServiceStockageAnnotations", "documentCollection"))
        self.d.connect()

    def test_connect(self):
        self.assertEqual(self.d.isConnected(), True)

    def l(self, strContent):
        # shortcut to load json
        return json.loads(strContent)

    def test_createMongoDocument(self):
        # try:
        #    self.d.createMongoDocument(None)
        # except MongoDocumentException,e:
        #    logging.info("working")
        self.assertRaises(MongoDocumentException, lambda: self.d.createMongoDocument(None))
        self.assertRaises(MongoDocumentException, lambda: self.d.createMongoDocument(self.l("{}")))
        id = self.d.createMongoDocument(self.l('{"@context":"testing_context"}'))
        self.assertTrue(id != "", "Object id must be not null %s" % (id))
        id = self.d.createMongoDocument(self.l('{"_id" : "yolo", "@context":"testing_context"}'))
        self.assertTrue(id != "yolo",
                        "Created id :%s should be different from the id in the document, since we ignore it." % (id))

    def test_getMongoDocument(self):
        self.assertEqual(None, self.d.getMongoDocument(None), "Null document should return nothing")
        self.assertEqual(None, self.d.getMongoDocument(""), "Bad id should return nothing")
        self.assertEqual(None, self.d.getMongoDocument("`&*%&^%&"), "Bad id should return nothing")
        # TODO: add security test later on
        context = "testing_context_%f" % random.random()
        docContent = '{"@context":"%s"}' % context
        id = self.d.createMongoDocument(self.l(docContent))
        self.assertTrue(id != None, "Object id must be not null %s" % (id))
        gotDocument = self.d.getMongoDocument(id)
        doc = self.assertNotEqual(None, gotDocument, "Should be a valid object" + str(gotDocument))
        self.assertTrue('@context' in gotDocument, "Document should have a context key")
        self.assertEqual(gotDocument['@context'], context, "Document should have context")
        self.assertEqual(id, gotDocument['_id'], "Document id should be the same")

    def test_updateMongoDocument(self):
        # try:
        #    self.d.createMongoDocument(None)
        # except MongoDocumentException,e:
        #    logging.info("working")
        self.assertRaises(MongoDocumentException, lambda: self.d.updateMongoDocument(None))
        self.assertRaises(MongoDocumentException, lambda: self.d.updateMongoDocument(self.l("{}")))
        id = self.d.createMongoDocument(self.l('{"@context":"testing_context"}'))
        self.assertTrue(id != "", "Object id must be not null %s" % (id))
        context = "testing_context_%f" % random.random()
        gotDocument = self.d.getMongoDocument(id)
        newStrDoc = '{"_id" : "%s" , "@context":"%s"}' % (id, context)
        id2 = self.d.updateMongoDocument(self.l(newStrDoc))
        self.assertEqual(id, id2, "Initial and update ids must be equal %s, %s" % (id, id2))
        gotDocument = self.d.getMongoDocument(id2)
        self.assertEqual(gotDocument['@context'], context,
                         "The initial document should have been updated: %s vs %s" % (gotDocument['@context'], context))
        id = "random_%f" % random.random()
        newStrDoc = '{"_id" : "%s" , "@context":"%s"}' % (id, context)
        self.assertRaises(MongoDocumentException, lambda: self.d.updateMongoDocument(self.l(newStrDoc)))

    def test_deleteMongoDocument(self):
        self.d.deleteMongoDocument("yolo")
        self.assertFalse(self.d.deleteMongoDocument("yolo"),
                         "Such a document should not exits, since we are deleting it a second time")
        id = self.d.createMongoDocument(self.l('{"@context":"testing_context"}'))
        self.assertTrue(id != "", "Object id must be not null %s" % (id))
        self.assertTrue(self.d.deleteMongoDocument(str(id)), "Delete should have been successful")
        self.assertEqual(None, self.d.getMongoDocument(id), "The document should have been deleted")

    def test_deleteMongoDocuments(self):
        id1 = self.d.createMongoDocument(self.l('{"@context":"testing_context","f1" : 1}'))
        id2 = self.d.createMongoDocument(self.l('{"@context":"testing_context","f1" : 2}'))
        id3 = self.d.createMongoDocument(self.l('{"@context":"testing_context","f1" : 3}'))
        # Delet all the documents with id greater then 1
        count = self.d.deleteMongoDocumentS(self.l('{"f1": {"$gt": 1 }}'))
        self.assertEqual(count, 2, "Should have deleted 2 documents, insted deleted {0}".format(count))
        self.assertEqual(None, self.d.getMongoDocument(id3), "Should have been deleted")
        self.assertNotEqual(None, self.d.getMongoDocument(id1), "Should exist")


if __name__ == '__main__':
    unittest.main()
