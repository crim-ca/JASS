import unittest
import simplejson
import logging
import random
import os
from pymongo import MongoClient

from jass.annotations_manager import AnnotationManager
from jass import settings
from jass.storage_exception import *

#other useful tools.

class TestAnnotationsManager(unittest.TestCase):
    d = None
    def setUp(self):
        settings.Settings.Instance().LoadConfig(os.path.join(os.path.dirname(__file__),"..","..","configs","test","config.ini"))
        
        c = MongoClient(settings.GetConfigValue("ServiceStockageAnnotations","MONGO_HOST"),
                                      int(settings.GetConfigValue("ServiceStockageAnnotations","MongoPort")))
        c.drop_database(settings.GetConfigValue("ServiceStockageAnnotations","MongoDb"))
        c.close()
        self.d = AnnotationManager()
        self.d.setCollection(settings.GetConfigValue("ServiceStockageAnnotations","HumanAnnotationCollection"))
        self.d.addStorageCollection(1,settings.GetConfigValue("ServiceStockageAnnotations","HumanAnnotationCollection"))
        self.d.addStorageCollection(2,settings.GetConfigValue("ServiceStockageAnnotations","BatchAnnotationCollection"))
        self.d.connect()
        
    def test_connect(self):
        self.assertEqual(self.d.isConnected(),True)
        
    def l(self,strContent):
        #shortcut to load json
        return simplejson.loads(strContent)
        

    def test_createAnnotationsS(self):
        jsonBatch = self.l('{"common":{"@context":"test"},"data":[{"a":1},{"b":2}]}')
        id = self.d.createMongoDocument(self.l('{"@context":"testing_context"}'))
        self.assertRaises(AnnotationException,lambda: self.d.createAnnotationS(jsonBatch, "yolo",1,1))  #bad id
        self.assertRaises(AnnotationException,lambda: self.d.createAnnotationS(jsonBatch, id,1,3))  #bad storage
        self.assertRaises(AnnotationException,lambda: self.d.createAnnotationS(jsonBatch, id,1,0))  #bad storage
        self.assertRaises(AnnotationException,lambda: self.d.createAnnotationS(jsonBatch, id,2,1))  #Bad format
        self.assertEqual(0,self.d.createAnnotationS(self.l("{}"),id))
        jsonInvalidBatch = self.l('{"data":[{"a":1,"@context":"test"},{"b":2}]}')
        self.assertRaises(AnnotationException,lambda: self.d.createAnnotationS(jsonInvalidBatch, id,1,1))
        jsonBatch = self.l('{"data":[{"a":1,"@context":"test"},{"b":2,"@context":"test"}]}')
        resDifferentBatchFormat =self.d.createAnnotationS(jsonBatch,id,0,2) 
        self.assertEqual(2,resDifferentBatchFormat,"Expected to get 2, but got {0} created with batch format 0".format(resDifferentBatchFormat))
    
    def test_getAnnotationsS(self):
        id = self.d.createMongoDocument(self.l('{"@context":"testing_context"}'))
        id2 = self.d.createMongoDocument(self.l('{"@context":"testing_context"}'))
        jsonBatch = self.l('{"common":{"@context":"test"},"data":[{"a":1,"b":1},{"a":2,"b":1}]}')
        jsonBatch2 = self.l('{"common":{"@context":"test"},"data":[{"a":1,"c":1},{"a":2,"c":1}]}')
        self.assertEqual(2,self.d.createAnnotationS(jsonBatch,id,1,1))
        self.assertEqual(2,self.d.createAnnotationS(jsonBatch2,id2,1,1))
        #
        res = self.d.getAnnotationS([id],{},0,1)
        self.assertEqual(2,len(res["data"]))
        res = self.d.getAnnotationS([id],{"a":1},0,1)
        self.assertEqual(1,len(res["data"]),"Filter a:1 for one docs should return 1 result. Results: {0}".format(str(res)))
        
        res = self.d.getAnnotationS([id,id2],{"a":1},0,1)
        self.assertEqual(2,len(res["data"]),"Filter a:1 for two docs should return 2 result. Results: {0}".format(str(res)))
        
        largeJsonBatch = self.l('{"common":{"@context":"test"},"data":[{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3},{"e":1},{"e":2},{"e":3}]}')
        
        self.assertEqual(27,self.d.createAnnotationS(largeJsonBatch,id2,1,1))
        res = self.d.getAnnotationS([id,id2],{"e":{"$gt" : 0}},0,1)
        self.assertEqual(27,len(res["data"]),"Filter e:1 for largebatch should return 27 result. Returned: {0}".format(len(res["data"])))
        #testing by getting
        #Change for large batch
        largeJsonBatch1 = self.l('{"common":{"@context":"test","k":1},"data":[{"a":1,"b":1},{"a":2,"b":1},{"a":3,"b":1}]}')
        largeJsonBatch2 = self.l('{"common":{"@context":"test","k":2},"data":[{"a":4,"c":1},{"a":5,"c":1}]}')
        largeJsonBatch3 = self.l('{"common":{"@context":"test","k":2},"data":[{"a":1,"c":1},{"a":2,"c":1},{"a":3,"c":1},{"a":4,"c":1}]}')
        # id, 2 batches total 5 anno
        # id2, 1 batch total 4 anno 
        self.assertEqual(3,self.d.createAnnotationS(largeJsonBatch1,id,1,2))
        self.assertEqual(2,self.d.createAnnotationS(largeJsonBatch2,id,1,2))
        self.assertEqual(4,self.d.createAnnotationS(largeJsonBatch3,id2,1,2))
        #get all annotations in both documents
        res = self.d.getAnnotationS([id,id2],{},0,2)
        self.assertEqual(9,len(res["data"]))
        #get all annotations of doc with id
        res = self.d.getAnnotationS([id],{},0,2)
        self.assertEqual(5,len(res["data"]))
        res = self.d.getAnnotationS([id],{"k":2},0,2)
        self.assertEqual(2,len(res["data"]))
        # get all batch annotations with key k = 2 for both documents
        res = self.d.getAnnotationS([id,id2],{"k":2},0,2)
        self.assertEqual(6,len(res["data"]))
        
    def test_deleteAnnotationsS(self):
        id = self.d.createMongoDocument(self.l('{"@context":"testing_context"}'))
        jsonBatch = self.l('{"common":{"@context":"test"},"data":[{"a":1},{"b":2}]}')
        jsonLargeBatch1 = self.l('{"common":{"@context":"test","batch":1},"data":[{"a":1},{"b":2}]}')
        jsonLargeBatch2 = self.l('{"common":{"@context":"test","batch":2},"data":[{"a":1},{"b":2}]}')
        self.assertEqual(0,self.d.deleteAnnotationS([id], {}))      
        self.assertEqual(2,self.d.createAnnotationS(jsonBatch,id))
        self.assertEqual(2,self.d.deleteAnnotationS([id], {}))
        self.assertEqual(2,self.d.createAnnotationS(jsonBatch,id,1,1))
        self.assertEqual(2,self.d.createAnnotationS(jsonLargeBatch1,id,1,2))
        res = self.d.deleteAnnotationS([id],{},1)
        self.assertEqual(2,res,"Should only delete 2 since we created 2 per storage type, but we got {0}".format(res))
        res = self.d.deleteAnnotationS([id],{},2)
        self.assertEqual(1,res,"Should delete 1 since we only have one batch".format(res))
        self.assertEqual(2,self.d.createAnnotationS(jsonLargeBatch1,id,1,2))
        self.assertEqual(2,self.d.createAnnotationS(jsonLargeBatch2,id,1,2))
        res = self.d.deleteAnnotationS([id],{"batch":1},2)
        self.assertEqual(1,res,"Should delete 1 (only the first batch of 2 batches) we got {0}".format(res))
        
if __name__ == '__main__':
    unittest.main()