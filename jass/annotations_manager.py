#!/usr/bin/env python
# coding:utf-8

import mongo_utils
import settings
import custom_logger as logger
from storage_exception import *
from bson.errors import *
from storage_manager import StorageManager
from bson.objectid import ObjectId
import gridfs
import simplejson

# MongoDB: some interesting performance statistics
# http://blog.mongolab.com/2014/01/how-big-is-your-mongodb/

# The question is what kind of manipulations should we allow for batch
# elements. For the moment, I will only put Create and Delete.

# I will have to check the python driver for unique object ids.

class AnnotationManager(StorageManager):

    ALL_STORAGE = 0         # Use all storage
    # Storage for human annotations. Every annotations is stored as a record
    HUMAN_STORAGE = 1
    # Storage for batch annotations. Annotations are grouped in batch (FUTURE).
    # Currently same as 1.
    BATCH_STORAGE = 2

    # Describes the format of the elements to input
    """
    ::
    
        {data:[{annotation1}...{annotationN}]}
            Where: annotation1 is the same format as if you would only get one
                   annotation
    """
    BASIC_BATCH_FORMAT = 0

    """
    ::
    
        {
            common: {
        
            }
            data : [{annotation1, ...}]
        }
    
    **common** : Elements contained in common will be copied for each annotation
    **annotation1** : Annotation specific information
    """
    COMPACT_BATCH_FORMAT = 1

    def addStorageCollection(self, storageType, collectionName):
        """
        Since we may have different collections depending on the type of
        storage we need a keypair value.
        """
        if not hasattr(self, 'storageCollections'):
            self.storageCollections = {}

        self.storageCollections[storageType] = collectionName

    def createAnnotation(self, jsonDoc, strDocId, storageType=1):
        """
        This function creates an annotation. Currently this only works for annotations in storageType = 1

        @Preconditions:
            documentId : A valid storage id. (We don't check that it exists
                         however). documentId will be added to the annotation
                         object as doc_id (or overwrite existing field).

        For the rest check createMongoDocument(self,jsonDoc,coll).
        """

        self.__validateStorageByType(storageType)

        if not mongo_utils.isObjectId(strDocId):
            logger.logInfo(AnnotationException(1, strDocId))
            raise AnnotationException(1, strDocId)

        if(jsonDoc is None):
            raise MongoDocumentException(2)

        jsonDoc['doc_id'] = strDocId
        return self.createMongoDocument(jsonDoc,
                                        self.storageCollections[storageType])

    def getAnnotation(self, strAnnoId, storageType=1):
        """
        Currently this only works for annotations in storageType = 1

        See getMongoDocument(self,strDocId,coll).
        """
        return self.getMongoDocument(strAnnoId,
                                     self.storageCollections[storageType])

    def deleteAnnotation(self, strAnnoId, storageType=1):
        """
        Currently this only works for annotations in storageType = 1

        See deleteMongoDocument(self,strDocId,coll) for more info.
        """
        return self.deleteMongoDocument(strAnnoId,
                                        self.storageCollections[storageType])

    def updateAnnotation(self, jsonDoc, strDocId, storageType=1):
        """
        This function updates an annotation.
        Currently this only works for annotations in storageType = 1.

        @Preconditions:
            documentId : A valid storage id. (we don't check that it exists
                         however). strDocId will be added to the annotation
                         object as doc_id (or overwrite existing field).
        """

        if not mongo_utils.isObjectId(strDocId):
            logger.logInfo(AnnotationException(1, strDocId))
            raise AnnotationException(1, strDocId)

        if(jsonDoc is None):
            raise MongoDocumentException(2)

        jsonDoc['doc_id'] = strDocId
        return self.updateMongoDocument(jsonDoc)

    def createAnnotationS(self,
                          jsonBatch,
                          strDocId,
                          batchFormat=1,
                          storageType=1):
        """
        Inserts annotations by batch. All annotations must be valid. Raises an
        error if there is even a single invalid annotation.

        A valid annotation after processing has the following attributes:
            :doc_id: Describes the id of the document containing the
                    annotation. Equals to strDocId.
            :@context: A field linking the context of the document.

            This field will be automatically created.
            _id:  A unique id identifying the annotation,


        :@param jsonBatch : JSON of the message. See batch format on how this
                            field is supposed to be structured.

        :@param strDocId : Id of the document containing the annotation
        :@param storageType : Describes how to store the elements. (Currently can not be changed) Supports: 1,2

        :@param batchFormat : Describes the format of the elements to input.
                              Supports: 0,1


        @return: Number of created annotations.

        """
        if(not mongo_utils.isObjectId(strDocId)):
            logger.logInfo(AnnotationException(1, strDocId))
            raise AnnotationException(1, strDocId)

        self.__validateStorageByType(storageType)

        # We do not support you can not create in all storages.
        if(storageType == AnnotationManager.ALL_STORAGE):
            logger.logError(AnnotationException(7, storageType))
            raise AnnotationException(7, storageType)

        # If the batch doesn't have data
        if 'data' not in jsonBatch:
            return 0

        if(batchFormat != AnnotationManager.COMPACT_BATCH_FORMAT and
           batchFormat != AnnotationManager.BASIC_BATCH_FORMAT):
            logger.logInfo(AnnotationException(5, batchFormat))
            raise AnnotationException(5, batchFormat)

        batchData = jsonBatch['data']
        if (batchFormat == AnnotationManager.COMPACT_BATCH_FORMAT):
            if 'common' in jsonBatch:
                batchCommon = jsonBatch['common']
                # Optimisations later
                for anno in batchData:
                    for common in batchCommon:
                        anno[common] = batchCommon[common]

        for anno in batchData:
            # We don't want the client to specify an id.
            if '_id' in anno:
                del anno["_id"]
            
            if '@context' not in anno:
                logger.logInfo(AnnotationException(4, str(anno), strDocId))
                raise AnnotationException(4, str(anno), strDocId)

        if(self.isConnected()):
            try:
                #make each annotation reference its document
                for anno in batchData:
                    anno['doc_id'] = strDocId
                
                db = self.client[self.mongoDb]
                coll = db[self.storageCollections[storageType]]
                if(storageType == 1):
                    # Insert annotations one by one. 
                    nbAnnoToInsert = len(batchData)
                    nbInserted = len(coll.insert(batchData))
                    if (nbAnnoToInsert != nbInserted):
                        # TODO: Delete all annotations if this happens
                        raise AnnotationException(8, nbInserted, nbAnnoToInsert)
                    
                    return nbInserted
                else: #Batch storage, save as files
                    fs = gridfs.GridFS(db) 
                    batchDoc = {}
                    for anno in batchData:  
                        if(batchDoc == {}): #Possible common attributes between annotations.
                            for attrib in anno:
                                batchDoc[attrib] = anno[attrib]
                                
                        # IF an annotation have a different value for an attribute, then the 
                        # common attribute, the common attribute must be deleted.
                        for attrib in anno:
                            if(str(attrib) in batchDoc):
                                if(anno[attrib] != batchDoc[str(attrib)]):    
                                    del batchDoc[attrib]
                                    
                        #Add id
                        anno["id"] = str(ObjectId())
                        
                    jsonDump = simplejson.dumps(batchData)
                    annoFileID = fs.put(jsonDump)
                    nbInserted = len(batchData)
                    if 'common' in jsonBatch:
                        batchCommon = jsonBatch['common']
                        for common in batchCommon:
                            batchDoc[common] = batchCommon[common]
                    
                    batchDoc['doc_id'] = str(strDocId)
                    batchDoc['file_fs_id_batch'] = annoFileID
                    try:
                        batch_id = coll.insert(batchDoc)
                    except Exception,e:
                        #clean up file info so we dont have garbage in our db
                        logger.logUnknownError("Annotation Storage Create Annotations","", e)
                        fs.delete(annoFileID)
                        raise MongoDocumentException(0)
                    
                    return nbInserted
            except AnnotationException, e:
                logger.logError(e)
                raise e

            except Exception, e:
                logger.logUnknownError("Annotation Storage Create Annotations",
                                       "", e)
                raise MongoDocumentException(0)
        else:
            raise StorageException(1)
        
    def replaceAnnotationsInLargeStorage(self,
                          jsonBatch,
                          strDocId,
                          batchFormat=1):
        """
        Create or replace batch annotations. Only works for batches present in large storage.
        This will first delete any batches (either the default batch, or batches returned by 
        "common" section. Then it will create the new batch.
        
        see createAnnotationS, deleteAnnotationS for more details.
        """
        jsonSelect = {}
        if(batchFormat == 1):
            if 'common' in jsonBatch:
                batchCommon = jsonBatch['common']
                for common in batchCommon:
                    jsonSelect[common] = {"$eq" : jsonBatch['common']}
        
        self.deleteAnnotationS([strDocId], jsonSelect, AnnotationManager.BATCH_STORAGE)
        return self.createAnnotationS(jsonBatch, strDocId, batchFormat, 
                                      AnnotationManager.BATCH_STORAGE)

    def getAnnotationS(self,
                       documentIds,
                       jsonSelect={},
                       batchFormat=0,
                       storageType=0):
        """
        Returns annotations respecting serach criterias

        :@param documentIds: List of documents containing the annotations.
        
        :@param jsonSelect: Additional query parameters, which can restrict the search: See: http://docs.mongodb.org/manual/reference/operator/query/ for options
        
        :@param storageType: Describe which annotation storage to search. Supports: 0,1,2
        
        :@param batchFormat: Describes how the elements would be returned Supports : 0

        :@return: Documents found. Return format is described by batchFormat.
        """
        if not (self.__validateDocumentIds(documentIds)):
            return {"data": []}

        # This will change later on.
        arr = []

        # Used to add a prefix to indicate BATCH_STORAGE, but removed it, since
        # It is the user job to manage them.
        if (storageType == AnnotationManager.ALL_STORAGE or 
            storageType == AnnotationManager.HUMAN_STORAGE):
            self.__setDocIdToJsonSelect(documentIds,jsonSelect)
            cursor = self.getMongoDocumentS(jsonSelect,
                                        self.storageCollections[AnnotationManager.HUMAN_STORAGE])
            for anno in cursor:
                anno["id"] = str(anno['_id'])
                del anno["_id"]
                arr.append(anno)
        if (storageType == AnnotationManager.ALL_STORAGE or 
            storageType == AnnotationManager.BATCH_STORAGE):
            self.__setDocIdToJsonSelect(documentIds,jsonSelect)
            cursor = self.getMongoDocumentS(jsonSelect,
                                        self.storageCollections[AnnotationManager.BATCH_STORAGE])
            for batch in cursor:
                db = self.client[self.mongoDb]
                fs = gridfs.GridFS(db)
                annotations = {}
                if(fs.exists(batch["file_fs_id_batch"])):
                    annotations = simplejson.loads(fs.get(batch["file_fs_id_batch"]).read())
                arr += annotations    
    
        return {"data": arr}

    def deleteAnnotationS(self, documentIds, jsonSelect={}, storageType=1):
        """
        Delete multiple annotations.

        :@param documentIds: List of documents containing the annotations.
        
        :@param jsonSelect: Additional query parameters, which can restrict the search: See: http://docs.mongodb.org/manual/reference/operator/query/ for options
        
        :@param storageType: Describe which annotation storage to search. Supports: 0,1,2
        
        :@param batchFormat: Describes how the elements would be returned Supports : 0

        :@return: Number of documents deleted.
        """
        if not (self.__validateDocumentIds(documentIds)):
            return 0

        self.__validateStorageByType(storageType)

        # This will change later on.
        count = 0
        self.__setDocIdToJsonSelect(documentIds,jsonSelect)
        print jsonSelect
        if (storageType == AnnotationManager.HUMAN_STORAGE or 
            storageType == AnnotationManager.ALL_STORAGE):
            count += self.deleteMongoDocumentS(jsonSelect,
                        self.storageCollections[AnnotationManager.HUMAN_STORAGE])
        if (storageType == AnnotationManager.BATCH_STORAGE or 
            storageType == AnnotationManager.ALL_STORAGE):
            #find all batches, delete batch content, then delete batch.
            batchDocs = self.getMongoDocumentS(jsonSelect,
                                   self.storageCollections[AnnotationManager.BATCH_STORAGE])
            print jsonSelect
            db = self.client[self.mongoDb]
            fs = gridfs.GridFS(db)
            #delete all the files
            for batch in batchDocs:
                try:
                    annoFileID = batch["file_fs_id_batch"]
                    if(fs.exists(annoFileID)):
                        fs.delete(annoFileID)
                except Exception,e:
                    #clean up file info so we dont have garbage in our db
                    logger.logUnknownError("Annotation Storage Delete Annotations","", e)
            #delete all the batches
            count += self.deleteMongoDocumentS(jsonSelect, 
                                   self.storageCollections[AnnotationManager.BATCH_STORAGE])
            
        return count

    # ~ Private
    def __setDocIdToJsonSelect(self, documentIds,jsonSelect):
        """
        set a filter by doc id  
        """
        if "doc_id" in jsonSelect:
            del jsonSelect["doc_id"]
            
        if "file_fs_id_batch" in jsonSelect:
            del jsonSelect["file_fs_id_batch"]
        
        docs = []
        for docId in documentIds:
            docs.append(str(docId))
        
        try:
            jsonSelect["doc_id"] = {"$in": docs}
        except Exception, e:
            logger.logUnknownError("Annotation Storage Get Doc Id", "Failed Delete Query", e)

    # ~ Private
    def __validateDocumentIds(self, documentIds):
        """
        :@param documentIds: List of documents containing the annotations.
                             Raises an exception if documentIds contains an
                             invalid Id
                             (Invalid Format, not whenever it exists or not).
        :@return: 0 if documentIds is empty.
        """
        if not (type(documentIds) is list):
            return 0

        if(len(documentIds) == 0):
            return 0

        for docId in documentIds:
            if(not mongo_utils.isObjectId(docId)):
                logger.logInfo(AnnotationException(3, docId))
                raise AnnotationException(3, docId)

        return 1

    def __validateStorageByType(self, storageType):
        if(storageType < AnnotationManager.ALL_STORAGE or
           storageType > AnnotationManager.BATCH_STORAGE):
            logger.logError(AnnotationException(7, storageType))
            raise AnnotationException(7, storageType)

        # Check for all storage types requirements.
        if(storageType == AnnotationManager.ALL_STORAGE):
            for storageType in [AnnotationManager.HUMAN_STORAGE,
                                AnnotationManager.BATCH_STORAGE]:
                if storageType not in self.storageCollections:
                    logger.logError(AnnotationException(6, storageType))
                    raise AnnotationException(6, storageType)
        else:
            if storageType not in self.storageCollections:
                logger.logError(AnnotationException(6, storageType))
                raise AnnotationException(6, storageType)
