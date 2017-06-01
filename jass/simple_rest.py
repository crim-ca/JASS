#!/usr/bin/env python
# coding:utf-8

"""
This module defines a REST API for the annotation storage service as defined by the CANARIE API specification.

===========
ANNOTATIONS
===========

There are several common concepts shared used in annotations, which we should describe here
    |        **reservedFields**:
    |            fields: "_id" is reserved and will be ignored if passed either inside annotation or document.
    |        **storageType**: Describe with which annotation storage we are
    |                         interacting. Multiple storages are required
    |                         Depending on the access of annotations.
    |                Values: 
    |                        **0**: All storage types
    |                        **1**: Human Storage : Storage used for small amount
    |                                           of annotations made by humans.
    |                                           Fast search, insert, delete,
    |                                           update.(Great performance degradation,
    |                                           if more then 10 millions annotations).
    |                        **2**: Large Storage : Storage used for large amount
    |                                           of annotations (like automatic
    |                                           annotations), which are not meant
    |                                           to be used individually. Very fast search,
    |                                           but can only operate on groups of annotations
    |                                           on fields defined in common fields).
    |                                           If no common field supplied.
    |                                           
    |
    |        **batchFormat**: Describe the format in which multiple annotations
    |                         should be send to the system. This also includes
    |                         how multiple annotations should be extracted from
    |                         the system.
    |                Values: 
    |                        **0**: {"data" : [{annotation1}...{annotationN}]}
    |                            Where: annotation1 is the same format as if
    |                            you would request 1 annotation
    |                        **1**: {
    |                                common: {
    |
    |                                }
    |                                data : [{annotation1, ...}]
    |                            }
    |
    |                            common : elements contained in common will be
    |                                     copied for each annotation
    |                            annotation1: annotation specific information
    |        **jsonSelect**: A jsonQuery to get a subset of annotations. See
    |                        for query variables:
    |                        See http://docs.mongodb.org/manual/reference/operator/query/
    |                        for options

===========
ERROR CODES
===========

Here is the prefix by type:
    ========================  ============= ====================================================
    Exception Type            Starting Code Reference Document
    ========================  ============= ====================================================
    UnknownException          50000         Unknown server crash error
    StorageRestExceptions     50100         :py:class:`storage_exception.StorageRestExceptions`
    AnnotationException       51000         :py:class:`storage_exception.AnnotationException`
    MongoDocumentException    52000         :py:class:`storage_exception.MongoDocumentException`
    StorageException          53000         :py:class:`storage_exception.StorageException`
    ========================  ============= ====================================================
"""

# -- Standard lib ------------------------------------------------------------
import optparse
import logging
import collections
import json
import os
import http.client

# -- 3rd party ---------------------------------------------------------------
from flask import Flask
from flask import request, current_app
from flask import render_template
from flask import jsonify

# Utility
from jass.utility_rest import request_wants_json
from jass.utility_rest import get_canarie_api_response
from jass.utility_rest import error_response  # OK

# -- Project specific --------------------------------------------------------
import jass.settings
import jass.error

# -- Program Classes --------------------------------------------------------
from jass.storage_exception import *
from jass.document_manager import DocumentManager
from jass.storage_manager import StorageManager
from jass.annotations_manager import AnnotationManager
import jass.custom_logger as logger
from werkzeug.exceptions import BadRequest
from jass.reverse_proxied import ReverseProxied
import jass.settings as settings

# -- Configuration -----------------------------------------------------------

FILE_ROOT = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(FILE_ROOT, "..", "templates")

APP = Flask(__name__,
            static_folder=os.path.join(FILE_ROOT, "..", "static"),
            template_folder=TEMPLATE_PATH)


# -- Accessibility ---------------------------------------------------------    --
# All the accessibility functions will be defined here

# ============================================================
#  Private
# ===========================================================


def _processCommonException(e):
    """
    This function is used to generate exception codes. It will create absolute
    codes for reference
    """
    if (isinstance(e, StorageException)):
        return error_response(http.HTTPStatus.SERVICE_UNAVAILABLE,
                              "Service Unavailable", 53000 + e.code,
                              "Error connecting to the backend storage")
    elif (isinstance(e, MongoDocumentException)):
        if (e.code == 0):
            return error_response(http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  "Internal Server Error", 52000,
                                  "Server can not currently process requests")
        else:
            return error_response(http.HTTPStatus.UNPROCESSABLE_ENTITY,
                                  "Cannot process Entity",
                                  52000 + e.code, str(e))
    elif (isinstance(e, AnnotationException)):
        if (e.code == 0):
            return error_response(http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  "Internal Server Error", 51000,
                                  "Server can not currently process requests")
        else:
            return error_response(http.HTTPStatus.UNPROCESSABLE_ENTITY,
                                  "Cannot process Entity", 51000 + e.code,
                                  str(e))
    elif (isinstance(e, StorageRestExceptions)):
        if (e.code == 2 or e.code == 3):
            return error_response(http.HTTPStatus.NOT_FOUND, "Not Found",
                                  50100 + e.code, str(e))
        else:
            return error_response(http.HTTPStatus.UNPROCESSABLE_ENTITY,
                                  "Cannot process entity", 50100 + e.code,
                                  str(e))
    elif (isinstance(e, BadRequest)):
        # Flask error
        return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")
    else:
        logger.logUnknownError("Annotation Storage REST Service Unknown Error",
                               str(e), 50000)
        return error_response(http.HTTPStatus.INTERNAL_SERVER_ERROR,
                              "Internal Server Error", "",
                              "Server can not currently process requests")


def _convStorageIdToDocId(doc):
    """
    Function convert doc to storageId.
    """
    if (not doc):
        return None
    if '_id' in doc:
        doc["id"] = doc["_id"]
        del doc["_id"]


def _convDocIdToStorageId(doc):
    """
    Function convert storageId to doc id.
    """
    if (not doc):
        return None
    if 'id' in doc:
        doc["_id"] = doc["id"]
        del doc["id"]


def _getStorageTypeFromId(strId):
    """
    Returns the storage type from object id.
    """
    if (strId is None or not type(strId) is 'str'):
        return -1

    if (strId.find("_") < 0):
        return AnnotationManager.HUMAN_STORAGE
    else:
        return AnnotationManager.BATCH_STORAGE


# -- Flask routes ------------------------------------------------------------
# TODO: add access validation.
# To the question of why using an ObjectId as document_id. Normally one would
# want to use the URL directly. However if 2 teams work on the same YouTube
# video, they may not necessarily want to share the annotations. (In fact it is
# possible, one group doesn't give the access right to another group).  Thus
# accessing a document via URL, will be given as a search option. I will also
# add a possibility to merge documents later on.

# Location: I was thinking if I should add location parameter to the objects.
# The idea is that in theory it should be possible to put lets say a
# document/schemas/annotations in different storages. However it is impractical
# for the following reasons:
#  1) Detection: Since document does not contain annotations, there is no
#                having a document to locate all its annotations, other then
#                creating an array to list them all.
#  2) Searching: Would be very annoying since we will have to check all the
#                listed annotations.
#  3) Security:  Would be hard to enforce
#
# Thus while it is possible to patch locations, we will assume all annotations
# for a particular document are located in the same storage

# Internal data: Reserving the use of i_a_s_d field for internal storage use.
# This may be needed later in order to differentiate the access of batch data
# vs normal data.

# The reason use PUT instead of POST:
# http://stackoverflow.com/questions/630453/put-vs-post-in-rest

# ==============================================================================
#  CANARIE Specific requests
# ==============================================================================

canarie_api_valid_requests = ['doc',
                              'releasenotes',
                              'support',
                              'source',
                              'tryme',
                              'licence',
                              'provenance']


@APP.before_request
def log_request():
    logger.logUnknownDebug("Annotation Storage Request url:", request.url)
    logger.logUnknownDebug("Annotation Storage Request type:", request.method)
    try:
        cl = request.content_length
        if cl is not None:
            if cl < 10000:
                logger.logUnknownDebug("Annotation Storage Request Data:", request.data)
            else:
                logger.logUnknownDebug("Annotation Storage Request Data:", " Too much data for output")
    except Exception as e:
        logger.logUnknownDebug("Annotation Storage Request Data:", "Failed to ouput data.")
    logger.logUnknownDebug("Annotation Storage Request Arguments:", request.args)


@APP.route("/info")
def info():
    """
    Required by CANARIE
    """
    canarie_config_section = "annotation_storage"

    service_info_categories = ['name',
                               'synopsis',
                               'version',
                               'institution',
                               'releaseTime',
                               'supportEmail',
                               'category',
                               'researchSubject']
    service_info = list()
    for category in service_info_categories:
        service_info.append((category,
                             settings.GetConfigValue(canarie_config_section, category)))

    service_info.append(('tags',
                         settings.GetConfigValue(canarie_config_section, 'tags').
                         split(',')))

    service_info = collections.OrderedDict(service_info)

    if request_wants_json():
        return jsonify(service_info)

    return render_template('default.html', Title="Info", Tags=service_info)


@APP.route("/stats")
def stats():
    """
    Required by CANARIE.
    """

    service_stats = {}
    if request_wants_json():
        return jsonify(service_stats)
    return render_template('default.html', Title="Stats", Tags=service_stats)


@APP.route('/home')
def home():
    """
    Return the home page for a particular service
    """
    canarie_config_section = "canarie_info"
    return get_canarie_api_response(canarie_config_section, TEMPLATE_PATH, 'home')


@APP.route("/<any(" +
           ",".join(canarie_api_valid_requests) + "):api_request>")
def simple_requests_handler(api_request):
    """
    Handle simple requests required by CANARIE
    """
    canarie_config_section = "canarie_info"
    return get_canarie_api_response(canarie_config_section, TEMPLATE_PATH, api_request)


# ==============================================================================
#  CANARIE END
# ==============================================================================

# ==============================================================================
#  Default error handlers.
# ==============================================================================
@APP.errorhandler(400)
def internal_error400(error):
    return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")


@APP.errorhandler(500)
def internal_error500(error):
    logger.logUnknownError("Annotation Storage REST Service Unknown Critical"
                           " Error", str(error), 50000)
    return error_response(http.HTTPStatus.INTERNAL_SERVER_ERROR,
                          "Internal Server Error", "",
                          "Server can not currently process requests")


# ==============================================================================
#  Appication Requests
# ==============================================================================

@APP.route('/document', methods=['POST'])
def createDocument():
    """
    :route: **/document**

    :POST creates a new document:
        :Request: 
        
            ::
            
                Preconditions: Here are the minimum required elements by the document.
                {
                    @context: context describing the format of the document
                }
            
            All the other parameters will be saved as is.
            Erases "_id", "id" fields if they exists.
        :Response: Same as in, plus creates a field "id" to identify the document
                
            :http status code:
                |    OK: 200
                |    Error: See Error Codes
    """
    man = DocumentManager()
    try:
        man.setCollection(settings.GetConfigValue("ServiceStockageAnnotations",
                                                  "documentCollection"))
        man.connect()
        if request.method == 'POST':
            docId = man.createMongoDocument(request.json)
            logger.logUnknownDebug("Create Document", "Id: {0}".format(docId))
            return jsonify({"id": docId}), 201
        else:
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

    except Exception as e:
        return _processCommonException(e)
    finally:
        man.disconnect()


# Not implemented things:
#     We have decided to not implement any validation for other elements,
#     since their presence does not affect the storage in any way.
#
#     Here is the list of the potential other elements
#     name:                   Name used to identify the document
#     target:                 Describes the resource this document is
#                             describing. Usually a URL like a link YouTube.
#     annotationSchemas:      An array containing a list of annotations
#                             schemas associated with this document.format
#                             for each ontology.
#                                 id:     ontology id ,
#                                 short_name: An alias which we will use to
#

@APP.route('/document/<document_id>', methods=['GET', 'PUT', 'DELETE'])
def document(document_id):
    """
    :route: **/document/<document_id>**

    Get/Put/Delete for the documents.

    :param document_id: The id of the document we want to access

    :GET returns a document:
        :Response  JSON:
        
            Here are minimum document contents:
            ::
                
                {
                  id:                    Id of the document = document_id
                  @context:              Complex object containing JSON_LD
                                         info.
                }

            Other custom fields which were created would be returned too.
                
            :http status code:
                |    OK: 200
                |    Error: See Error Codes

    :PUT updates a document by replacing whole document contents:
        :Request:
        
            The document must exists and contains the following contents at minimum:
            ::
            
                 {
                     id:                    Id of the document = document_id
                     @context:              Complex object containing JSON_LD
                                            info.
                 }
            
            Other custom fields which were created would be saved too.
            Erases "_id" field.
            
        :Response:
            :http status code:
                |    OK: 200
                |    Error: See Error Codes

    :DELETE deletes the document. If the document not found do nothing.:
        :Response JSON: {}
                   
            :http status code:
                |    OK: 200
                |    Error: See Error Codes
    """
    man = DocumentManager()
    try:
        man.setCollection(settings.GetConfigValue("ServiceStockageAnnotations",
                                                  "documentCollection"))
        man.connect()
        if request.method == 'GET':
            logger.logUnknownDebug("Get Document", "Id: {0}".format(document_id))
            doc = man.getMongoDocument(document_id)
            _convStorageIdToDocId(doc)
            if (doc is None):
                raise (StorageRestExceptions(2))
            else:
                return jsonify(doc)
        elif request.method == 'PUT':
            logger.logUnknownDebug("Update Document", "Document {0}".format(document_id))
            doc = request.json
            _convDocIdToStorageId(doc)
            if '_id' in doc and doc["_id"] != document_id:
                raise (StorageRestExceptions(1))
            else:
                docId = man.updateMongoDocument(doc)
                return jsonify({"id": docId})
        elif request.method == 'DELETE':
            logger.logUnknownDebug("Delete Document", "Id: {0}".format(document_id))
            man.deleteMongoDocument(document_id)
            # Whenever it is true or false we don't care, if there is no
            # exception
            return jsonify({}), 204
        else:
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

    except Exception as e:
        return _processCommonException(e)
    finally:
        man.disconnect()


@APP.route('/annotationSchema', methods=['POST'])
def createAnnotationSchema():
    """
    :route: **/annotationSchema**

    Used to store Annotation schemas
    Same implementation as for the document.
    """
    man = DocumentManager()
    try:
        man.setCollection(settings.GetConfigValue("ServiceStockageAnnotations",
                                                  "SchemaCollection"))
        man.connect()
        if request.method == 'POST':
            docId = man.createMongoDocument(request.json)
            logger.logUnknownDebug("Create Schema", "Id: {0}".format(docId))
            return jsonify({"id": docId}), 201
        else:
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

    except Exception as e:
        return _processCommonException(e)
    finally:
        man.disconnect()


@APP.route('/annotationSchema/<schema_id>', methods=['GET', 'PUT', 'DELETE'])
def annotationSchema(schema_id):
    """
    :route: **/annotationSchema/<schema_id>**

    Used to store annotation schemas.
    Same implementation as for the document.
    """

    man = StorageManager()
    try:
        man.setCollection(settings.GetConfigValue("ServiceStockageAnnotations",
                                                  "SchemaCollection"))
        man.connect()
        if request.method == 'GET':
            logger.logUnknownDebug("Get Schema", "Id: {0}".format(schema_id))
            doc = man.getMongoDocument(schema_id)
            _convStorageIdToDocId(doc)
            if (doc is None):
                raise (StorageRestExceptions(2))
            else:
                return jsonify(doc)
        elif request.method == 'PUT':
            doc = request.json
            _convDocIdToStorageId(doc)
            if '_id' in doc and doc["_id"] != schema_id:
                raise (StorageRestExceptions(1))
            else:
                logger.logUnknownDebug("Update Schema", "Id: {0}".format(schema_id))
                docId = man.updateMongoDocument(request.json)
                if (docId is None):
                    raise (StorageRestExceptions(3))
                return jsonify({"id": docId})
        elif request.method == 'DELETE':
            logger.logUnknownDebug("Delete Schema", "Id: {0}".format(schema_id))
            man.deleteMongoDocument(schema_id)
            # Whenever it is true or false we don't care, if there is no
            # exception
            return jsonify({}), 204
        else:
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

    except Exception as e:
        return _processCommonException(e)
    finally:
        man.disconnect()


@APP.route('/document/<document_id>/annotations',
           methods=['GET', 'PUT', 'POST', 'DELETE'])
def documentAnnotationS(document_id):
    """
    :route: **/document/<document_id>/annotations**

    In case storageType = 2, annotations will be stored in batches. All operations impact 
    each batch (Example a PUT operation will replace all annotations in a batch).
    By default each document have 1 annotation batch. To have multiple batches,
    post/put batch of annotations using batchFormat = 1, and use common section to
    to identify uniquely a batch. Fields "doc_id_batch", "file_fs_id_batch" are reserved,
    thus will be ignored if added in common section. 

    :param document_id: The id of the document from which we want to access
                        multiple annotations

    :POST Create annotations in batch.: 
        :Request:
 
            :preconditions:
            
               All must be valid annotations.
               If one annotation fails, it will return an error message and
               fail all create. 
            :params supported:
            
                |   batchFormat = 0,1
                |   storageType = 1,2
            :params default:
            
                |   batchFormat = 1
                |   storageType = 1
        :Response json:
        
            |    returns {"nInserted":nbAnnotationsInserted}
            
            :http status code:
                |    OK: 200
                |    Error: See Error Codes

    :PUT Updates annotations related for the document.: 
        :Request:
    
            When we update we replace old contents with new ones. jsonSelect 
            
            :params supported:
                |    jsonSelect (only contains contents in the "common" fields for storageType = 2.)
                |    storageType = 2
            
            :params default:
            
                |    storageType = 2 
                |    jsonSelect = {}
        :Response json:
            |    Returns number of annotations deleted
            |    {"nDeleted":nbAnnotationsDeleted}
            
            :http status code:
                |    OK: 200
                |    Error: See Error Codes

    :DELETE Deletes annotations related for the document.:
        :Request:
        
            :params supported:
            
                |    jsonSelect
                |    storageType = 1,2
            :params default:
            
                |    storageType = 1
                |    jsonSelect = {}
        :Response json:
            |    Returns number of annotations deleted
            |    {"nDeleted":nbAnnotationsDeleted}
            
            :http status code:
                |    OK: 200
                |    Error: See Error Codes

    :GET Returns annotations for the current document.:
        :Request:
        
            :params supported:
            
                |    jsonSelect
                |    storageType = 0,1,2
                |    batchFormat = 0
                
            :params default:
                |    batchFormat = 0
                |    storageType = 0
                |    jsonSelect = {}
        :Response json:
        
            An array of annotations check batch format for how they will be
            formatted.
            
            :http status code:
                |    OK: 200
                |    Error: See Error Codes


    """
    man = AnnotationManager()

    try:
        hac = settings.GetConfigValue("ServiceStockageAnnotations",
                                      "HumanAnnotationCollection")
        man.addStorageCollection(AnnotationManager.HUMAN_STORAGE, hac)
        bac = settings.GetConfigValue("ServiceStockageAnnotations",
                                      "BatchAnnotationCollection")
        man.addStorageCollection(AnnotationManager.BATCH_STORAGE, bac)
        man.connect()

        jsonSelect = request.args.get('jsonSelect')
        storageType = request.args.get('storageType')
        batchFormat = request.args.get('batchFormat')

        # Note for batch operations all ids are replaced in man
        if request.method == 'GET':
            try:
                if not jsonSelect:
                    jsonSelect = {}
                else:
                    jsonSelect = json.loads(jsonSelect)
                if not storageType:
                    storageType = 0
                else:
                    storageType = int(storageType)
                if not batchFormat:
                    batchFormat = 0
                else:
                    batchFormat = int(batchFormat)
            except Exception as e:
                raise (StorageRestExceptions(5))
            batch = man.getAnnotationS([document_id], jsonSelect, batchFormat,
                                       storageType)
            return jsonify(batch)

        elif request.method == 'PUT':
            logger.logUnknownDebug("Update Annotations", " For document Id: {0}".format(document_id))
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

        elif request.method == 'POST':
            jsonBatch = request.json
            try:
                if not storageType:
                    storageType = 1
                else:
                    storageType = int(storageType)
                if not batchFormat:
                    batchFormat = 1
                else:
                    batchFormat = int(batchFormat)
                logger.logUnknownDebug("Create Annotations",
                                       " For document Id: {0} StorageType :{1},BatchFormat:{2}, jsonBatch: {3}".format(
                                           document_id, str(storageType), str(batchFormat), str(jsonBatch)))
            except Exception as e:
                raise (StorageRestExceptions(5))

            nbAnnotationsCreated = man.createAnnotationS(jsonBatch,
                                                         document_id,
                                                         batchFormat,
                                                         storageType)
            return jsonify({"nCreated": nbAnnotationsCreated})

        elif request.method == 'DELETE':
            # Whenever it is true or false we don't care, if there is no
            # exception
            try:
                logger.logUnknownDebug("Delete Annotations", " For document Id: {0}".format(document_id))
                if not jsonSelect:
                    jsonSelect = {}
                else:
                    jsonSelect = json.loads(jsonSelect)
                if not storageType:
                    storageType = 0
                else:
                    storageType = int(storageType)
            except Exception as e:
                raise (StorageRestExceptions(5))

            nbAnnotationsDeleted = man.deleteAnnotationS([document_id],
                                                         jsonSelect,
                                                         storageType)
            logger.logUnknownDebug("Delete Annotations",
                                   " Number of deleted annotations {0} For document Id: {1}".format(
                                       str(nbAnnotationsDeleted), document_id))
            return jsonify({"nDeleted": nbAnnotationsDeleted}), 200
        else:
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

    except Exception as e:
        return _processCommonException(e)
    finally:
        man.disconnect()


# TODO Update
@APP.route('/document/<document_id>/annotation', methods=['POST'])
def createDocumentAnnotation(document_id):
    """
    :route: **/document/<document_id>/annotation**
    
    :param document_id: The id of the document for which we want to access the annotation

    :POST Creates an annotation.:
        :Request:
            :preconditions:
            
                Here are minimum annotations contents:
                ::
                
                    {
                      @context: Complex object containing JSON_LD info.
                    }
                    
                Other custom fields which were created would be returned too.
            
            The annotation using this method is created in HumanStorage.
        :Response JSON:
        
            Here are minimum annotations contents which will be after creation:
            ::
            
                 {
                    doc_id: to describe the id of the document containing the
                            annotation. Equals to strDocId.
                    @context: a field linking the context of the document.
                    id:  a unique id identifying the annotation.
                 }
                 
            :http status code:
                |    OK: 200
                |    Error: See Error Codes
    """
    man = AnnotationManager()
    hac = settings.GetConfigValue("ServiceStockageAnnotations",
                                  "HumanAnnotationCollection")
    man.addStorageCollection(AnnotationManager.HUMAN_STORAGE, hac)
    try:
        man.connect()
        if request.method == 'POST':
            logger.logUnknownDebug("Create Annotation", " For document Id: {0}".format(document_id))
            docId = man.createAnnotation(request.json, document_id)
            return jsonify({"id": docId}), 201
        else:
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

    except Exception as e:
        return _processCommonException(e)
    finally:
        man.disconnect()


@APP.route('/document/<document_id>/annotation/<annotation_id>',
           methods=['GET', 'PUT', 'DELETE'])
def documentAnnotation(document_id, annotation_id):
    """
    :route: **/document/<document_id>/annotation/<annotation_id>**

    Get/Update/Delete an annotation:

    :param document_id: The id of the document for which we want to access the
                        annotation
    :param annotation_id: The id of the annotation we want to access

    :GET Returns an annotation:
        :Request:
             :precondtions:
             
                 Can only get annotations from HumanStorage.
                 
        :Response json:
            
            Here are minimum annotations contents which will be after
            creation:
            ::
            
                {
                    doc_id: to describe the id of the document containing the
                            annotation. Equals to strDocId.
                    @context: a field linking the context of the document.
                    id:  a unique id identifying the annotation.
                }

    :PUT Updates an annotation:
        Updates are made by changing the content of the old annotation with the new one
        
        :Request:
            :precondtions:
                Can only get annotations from HumanStorage.
        :Response:
            :http status code:
                |    OK: 200
                |    Error: See Error Codes

    :DELETE deletes an annotation.:
        :Request:
             :precondtions:
                 Can only get annotations from HumanStorage.
                 
        :Response:
            :http status code:
                |    OK: 204
                |    Error: See Error Codes
    """
    man = AnnotationManager()

    try:

        hac = settings.GetConfigValue("ServiceStockageAnnotations",
                                      "HumanAnnotationCollection")
        man.addStorageCollection(AnnotationManager.HUMAN_STORAGE, hac)
        man.connect()
        if (not _getStorageTypeFromId(AnnotationManager.HUMAN_STORAGE)):
            raise (StorageRestExceptions(4))

        if request.method == 'GET':
            logger.logUnknownDebug("Get Annotation", " For document Id: {0}".format(document_id))
            doc = man.getAnnotation(annotation_id)
            _convStorageIdToDocId(doc)
            if (doc is None):
                raise (StorageRestExceptions(2))
            else:
                return jsonify(doc)
        elif request.method == 'PUT':
            doc = request.json
            _convDocIdToStorageId(doc)
            if '_id' in doc and doc["_id"] != annotation_id:
                raise (StorageRestExceptions(1))
            else:
                logger.logUnknownDebug("Update Annotation", " For document Id: {0}".format(document_id))
                man.updateAnnotation(doc, annotation_id)
                return jsonify({})
        elif request.method == 'DELETE':
            logger.logUnknownDebug("Delete Annotation", " For document Id: {0}".format(document_id))
            man.deleteAnnotation(annotation_id)
            # Whenever it is true or false we don't care, if there is no
            # exception
            return jsonify({}), 204
        else:
            return error_response(http.HTTPStatus.BAD_REQUEST, "Bad Request", "", "")

    except Exception as e:
        return _processCommonException(e)
    finally:
        man.disconnect()


if __name__ == "__main__":
    # -- Script entry point --------------------------------------------------
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    PARSER = optparse.OptionParser()
    PARSER.add_option('-p', '--port', dest='port', type=int, default=5000)
    PARSER.add_option('--host', dest='host', default="127.0.0.1")
    PARSER.add_option('-d', '--debug', action="store_true", dest='debug',
                      default=False)

    PARSER.add_option('--config',
                      dest="config_path",
                      default=os.path.join(os.path.dirname(FILE_ROOT), "configs", "dev", "config.ini"),
                      help='Configuration Directory')

    OPTS, ARGS = PARSER.parse_args()
    settings.Settings.Instance().LoadConfig(OPTS.config_path)
    # Setting manually mongo host


    APP.run(port=OPTS.port, debug=OPTS.debug, host=OPTS.host)
else:
    if os.environ.get('JASS_CONFIG_PATH') != None:
        APP.wsgi_app = ReverseProxied(APP.wsgi_app)
        settings.Settings.Instance().LoadConfig(os.environ['JASS_CONFIG_PATH'])
