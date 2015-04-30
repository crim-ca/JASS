===================================================
NEP-143-1 JASS (JSON-LD Annotation Storage Service)
===================================================    

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

The purpose of this application is to propose a rest API to store and manipulate very large amounts of
JSON_LD (json-ld.org) compliant annotations. Annotation are stored in a Mongo DB backend. 

------------
INSTALLATION
------------

See INSTALL.rst

-------------------
MAJOR FUNCTIONALITY
-------------------

There is 3 elements which are stored in annotation storage:

- Documents. A documents contains multiple annotations. 
- Annotations. An annotations describes the document it is contained in. 
	An annotation can not exist by itself
- Schema. Used to describe the structure of annotation. Usually used as JSON-LD context. 

Note that due to the choice of the back end storage the JSON content of a Document,Annotation or
Schema can not exceed 16 MB in size.

--------------------
STARTING APPLICATION
--------------------

If supervisor vas installed it will running by default.
For dev purposes it is easier to use local flask web server. 
For this:

Stop supervisor

.. code-block:: bash 

	sudo service supervisord start

Make sure mongo db is working

.. code-block:: bash

	sudo service mongod status

Run storage using flask build in server. This will make the server run on: http://127.0.0.1:5000

.. code-block:: bash

	cd $ANNO_STO_HOME
	python -m src/program/simple_rest --port 5000 --host "0.0.0.0" --env "dev" > /tmp/anno_storage_out.txt

Usage options
::
 
 --port, for the port on which the program will run
 --host, for the host on which the program will run.  0.0.0.0 to be accessed by everybody
 --env : configuration environnement. Will go to configs/<env> to get the installation config. 


===============
BASIC API USAGE
===============

| The procedure is to create a document, then add/delete annotations associated with the document
| Using curl http://curl.haxx.se/docs/ to call the api.

---------
DOCUMENTS
---------
*************************
Creating a basic document
*************************

.. code-block:: bash

	curl -v -H "Content-Type: application/json" -d '{"@context":"test","a":"a","b":"b"}' http://127.0.0.1:5000/document

| This will return a document id
| Ex:  **53fe308de1382336346f05f7**
| For the late usage replace the <document_id> with the id you have obtained here.

********************************
Get the document created earlier
********************************
.. code-block:: bash

	curl -v http://127.0.0.1:5000/document/<document_id>

***************************
Update the document content
***************************
:Note: When updating, the full content of the document is replaced. It is not currently possible to only update a part of a document. 


.. code-block:: bash

	curl -v -X PUT -H "Content-Type: application/json" -d '{"id":"<document_id>", "@context":"test","a":"a","c":"c"}' http://127.0.0.1:5000/document/<document_id>

===========
ANNOTATIONS
===========

**Annotations can be stored in 2 storage engines:** 

:Human Annotation Storage: Made for annotations which are normally viewed/manipulated by humans. These annotations can be accessed and modified one by one. Annotations in human annotation storage can be accessed/searched/created/modified/delete individually or by batches. All annotations are stored in human annotation storage by **default**. 

:Large Annotation Storage: Made for large amounts of annotations which are mostly used for preprocessing. These annotations can be accessed by batches. It is possible to create/search/remove batches of annotations. When creating a batch of annotations, fields common to all annotations can be used to search for the batch. 

See documentation for more info. 

:Note: Annotations manipulations can be done for annotations of one particular document at a time. This restriction was made for security and scalability issues.

------------------------
Human Annotation Storage
------------------------

**Creating one annotation**

.. code-block:: bash

		curl -v -H "Content-Type: application/json" -H "Accept: application/json" -d '{"@context":"test", "a":"15"}' http://127.0.0.1:5000/document/<document_id>/annotation

**Creating multiple annotations**
:Note: Information in the "common" information will be replicated to all annotations.

.. code-block:: bash

	curl -v -H "Content-Type: application/json" -H "Accept: application/json" -d '{"common":{"@context":"test"},"data":[{"a":1},{"b":"1"},{"a":1,"c":2}]}' http://127.0.0.1:5000/document/<document_id>/annotations

**Get all annotations** of the document, which contain field a equal to 1. 
:Note: to do so we add an optional search parameter **jsonSelect** and specify {"a" : 1}. The syntax from search is the same as for mongo db: http://docs.mongodb.org/manual/reference/method/db.collection.find/. By default get is not restricted to the storage (ie it will return annotations which satify the criteria from bot human and batch storages). Use parameter storageType=1 parameter to restrict search to only human annotation storage     

.. code-block:: bash

	curl -v -H "Accept: application/json" http://127.0.0.1:5000/document/<document_id>/annotations?jsonSelect=%7B%22a%22%3A1%7D&storageType=1

**Verify** that 4 annotations exists for this document

.. code-block:: bash

	curl -v -H "Accept: application/json" http://127.0.0.1:5000/document/<document_id>/annotations


**Delete all annotations** with value c equal to 2

.. code-block:: bash

	curl -v -X DELETE -H "Content-Type: application/json" -H "Accept:application/json" http://127.0.0.1:5000/document/<document_id>/annotations?jsonSelect=%7B%22c%22%3A2%7D

**Verify** that all annotations with value c equal to 2 are deleted.

.. code-block:: bash

	curl -v -H "Accept: application/json" http://127.0.0.1:5000/document/<document_id>/annotations


------------------------
Large Annotation Storage
------------------------

**Creating one batch** contatining multiple annotations

.. code-block:: bash

	curl -v -H "Content-Type: application/json" -H "Accept: application/json" -d '{"common":{"@context":"test"},"data":[{"d":1},{"d":1},{"d":1,"a":1}]}' http://127.0.0.1:5000/document/<document_id>/annotations?storageType=2

**Get all annotations** for the document. 

.. code-block:: bash

	curl -v -H "Accept: application/json" http://127.0.0.1:5000/document/<document_id>/annotations
	
**Get all annotations** only annotations from large storage     

.. code-block:: bash

	curl -v -H "Accept: application/json" http://127.0.0.1:5000/document/<document_id>/annotations?storageType=2
	
**Searching all annotations** with value a equals to 1. It is possible to see, that even if large storage contains, annotations with value, a = 1 ({"d":1,"a":1}), they can not be searched directly, a = 1 is not a common field of all annotations in the batch.     

.. code-block:: bash

	curl -v -H "Accept: application/json" http://127.0.0.1:5000/document/<document_id>/annotations?jsonSelect=%7B%22a%22%3A1%7D

**Searching all annotations** with value d equals to 1. It is possible to see that batch annotations are found.      

.. code-block:: bash

	curl -v -H "Accept: application/json" http://127.0.0.1:5000/document/<document_id>/annotations?jsonSelect=%7B%22d%22%3A1%7D
