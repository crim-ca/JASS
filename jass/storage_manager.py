import pymongo
import pymongo.errors
from pymongo import MongoClient
import jass.mongo_utils as mongo_utils
import jass.settings as settings
import jass.custom_logger as logger
from jass.storage_exception import *
from bson.objectid import ObjectId
from bson.errors import *

# MongoDB: some interesting performance statistics
# http://blog.mongolab.com/2014/01/how-big-is-your-mongodb/


class StorageManager:
    """
    Storage manager class.
    """
    m_connected = False

    def setCollection(self, collection):
        """
        Collection in which documents will be created/updated/destroyed.
        """
        self.mongoCollection = collection

    def connect(self):
        """
        Connects to MongoDB and verifies connection.
        """
        try:
            host = settings.GetConfigValue("ServiceStockageAnnotations", "MONGO_HOST")
            port = int(settings.GetConfigValue("ServiceStockageAnnotations", "MongoPort"))
            self.client = MongoClient(host, port, connect=False)
            db = settings.GetConfigValue("ServiceStockageAnnotations",
                                         "MongoDb")
            self.mongoDb = db

            # Force connection test
            # https://api.mongodb.com/python/current/migrate-to-pymongo3.html#mongoclient-connects-asynchronously
            self.client.admin.command("ismaster")

            self.m_connected = True
            return True

        except pymongo.errors.ConnectionFailure:
            logger.logError(StorageException(1))

        except Exception as e:
            logger.logUnknownError("Annotation Storage Create Document",
                                   "", e)
            self.m_connected = False
            return False

    def isConnected(self):
        """
        Connects to MongoDB and verifies connection.
        """
        return self.m_connected

    def createMongoDocument(self, jsonDoc, collection=None):
        """
        Creates a new document.
        This function only validates the presence of the required fields.

        :preconditions (Otherwise exception is thrown):
            * isConnected must be true,
            * jsonDoc must exist and be a valid JSON object,

        :param jsonDoc: Contents of the document as string
            Here are the elements required by the document:
            ::
            
                {
                    @context: context describing the format of the document
                }

            If the document contains the field _id, the _id field will be
            deleted and another _id field will be generated instead. The
            generated _id will be required to access the document.

         :param collection: Enables you to override the default collection if
                            needed

         :return _id: The ID of the created document
        """
        if not collection:
            collection = self.mongoCollection

        if self.isConnected():
            if jsonDoc is None:
                raise MongoDocumentException(2)
            # We don't want the client to specify an id.
            if '_id' in jsonDoc:
                del jsonDoc["_id"]
            try:
                db = self.client[self.mongoDb]
                coll = db[collection]
                doc_id = coll.insert(jsonDoc)
                return str(doc_id)
            except Exception as e:
                logger.logUnknownError("Annotation Storage Create Document",
                                       "", e)
                raise MongoDocumentException(0)
        else:
            raise StorageException(1)

    def getMongoDocument(self, strDocId, collection=None):
        """
        Returns a document
        This function only validates the presence of the required fields.

        :Preconditions (Otherwise exception is thrown):
            * isConnected must be true,

        :param strDocId: Document ID
        
        :return : If the document is found returns a json object of the
                  document, otherwise returns None

            Document content returned (mandatory). Other user fields may be present:
            ::
            
                {
                    _id: Document id as a string
                    @context: context describing the format of the document
                }
        """
        if not collection:
            collection = self.mongoCollection

        if self.isConnected():
            try:
                db = self.client[self.mongoDb]
                coll = db[collection]
                doc = coll.find_one({"_id": ObjectId(strDocId)})
                mongo_utils.changeDocIdToString(doc)
                return doc
            except InvalidId:
                return None
            except Exception as e:
                logger.logUnknownError("Annotation Storage Get Document",
                                       "", e)
                raise MongoDocumentException(0)
        else:
            raise StorageException(1)

    def updateMongoDocument(self, jsonDoc, collection=None):
        # Note for now: We just create a new document. Reason: Simpler
        """
        Updates an existing document, by replacing it with new contents.
        This function only validates the presence of the required fields.

        :Preconditions (Otherwise exception is thrown):
            * isConnected must be true,
            * required fields must be present

        :param jsonDoc: Document as a JSON document. The document needs to contain a valid id.

        :return : If the document to be updated is found, returns the id of the document. If it can not be found, raises an exception.

                  Document content returned (mandatory). Other user fields may be present:
                  ::
                  
                      {
                          _id: Document id as a string
                          @context: Context describing the format of the document
                      }
        """

        if not collection:
            collection = self.mongoCollection

        if self.isConnected():
            if jsonDoc is None:
                raise MongoDocumentException(2)

            if '_id' in jsonDoc:
                doWithId = self.getMongoDocument(jsonDoc['_id'])
                if doWithId is None:
                    # ID cannot be found
                    logger.logInfo(MongoDocumentException(5, jsonDoc['_id']))
                    raise MongoDocumentException(5, jsonDoc['_id'])

            else:
                logger.logInfo(MongoDocumentException(5, ""))
                raise MongoDocumentException(5, "")

            mongo_utils.changeDocIdToMongoId(jsonDoc)

            try:
                db = self.client[self.mongoDb]
                coll = db[collection]
                doc_id = coll.save(jsonDoc)
                return str(doc_id)
            except Exception as e:
                logger.logUnknownError("Annotation Storage Update Document",
                                       "", e)
                raise MongoDocumentException(0)

        else:
            raise StorageException(1)

    def deleteMongoDocument(self, strDocId, collection=None):
        """
        Deletes a document specified by ID.

        :param strDocId: Document ID as string. Should be unique.
        
        :returns: 0 if no elements were deleted, 1 if one was deleted.
        """

        if not mongo_utils.isObjectId(strDocId):
            return 0

        return self.deleteMongoDocumentS({"_id": ObjectId(strDocId)},
                                         collection)

    # Note this method should be considered protected

    def getMongoDocumentS(self, jsonQuery, collection=None):
        """
        Search a collection for documents.

        :@param documentIds: List of document IDs for which we should search annotations.
        
        :@param A queryToDetermine how to select annotations: see http://docs.mongodb.org/manual/reference/operator/query/ for options

        :@return the number of deleted documents
        """

        if not collection:
            collection = self.mongoCollection

        if self.isConnected():
            try:
                db = self.client[self.mongoDb]
                coll = db[collection]
                res = coll.find(jsonQuery)
                return res
            except StorageException as e:
                raise e
            except Exception as e:
                logger.logUnknownError("Annotation Storage Get Document",
                                       "", e)
                raise MongoDocumentException(0)

        else:
            raise StorageException(1)

    def deleteMongoDocumentS(self, jsonQuery, collection=None):
        """
        Delete multiple annotations.

        :@param documentIds: List of document IDs which should be affected.
        
        :@param a queryToDetermine how to select annotations: see http://docs.mongodb.org/manual/reference/operator/query/ for
            options

        :@return The number of deleted documents
        """

        if not (collection):
            collection = self.mongoCollection

        if self.isConnected():
            try:
                db = self.client[self.mongoDb]
                coll = db[collection]
                res = coll.remove(jsonQuery)
                if(res['ok'] != 1):
                    raise StorageException(2)
                else:
                    return res['n']
            except StorageException as e:
                raise e
            except Exception as e:
                logger.logUnknownError("Annotation Storage Delete Document",
                                       "", e)
                raise MongoDocumentException(0)

        else:
            raise StorageException(1)

    def disconnect(self):
        if self.isConnected():
            try:
                self.client.close()
                self.m_connected = False
            except:
                self.m_connected = False
