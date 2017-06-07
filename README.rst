============================================
NEP-143-1 Annotation Storage Service
============================================

The purpose of this Annotation Storage Service (JASS) is to offer a
REST API to store and manipulate large amounts of JSON annotations. Annotation are stored in a
MongoDB backend.
 
The documentation for this package lives `here
<http://services.vesta.crim.ca/docs/jass/latest/>`_.

-------
License
-------

See :ref:`LICENSE.rst <license_info>` file contents.

------------
Installation
------------

See :ref:`INSTALL.rst <install_directives>`.

---------------------
Major Functionalities
---------------------

There are 3 elements which are stored in the annotation storage:

- Documents. A document contains multiple annotations.
- Annotations. An annotation describes the document it is contained in. (An
  annotation cannot exist by itself)
- Schema. Used to describe the structure of an annotation.

Note that due to the choice of the storage back end the JSON content of a
Document, Annotation or Schema can not exceed 16 MB in size.

-----------------
Starting the JASS
-----------------

 1. Running with docker compose:
 2. Running JASS in a container

*****************************
Running with docker compose:
*****************************
After cloning the repository, go to the project root and execute

.. code-block:: bash

    docker-compose up -d

This command will create JASS and MongoDB containers and run them in background.
The first time this command is run, it will build MongoDB and JASS containers. Once the build is finished (the shell will resume), it will take approximately 30 seconds for JASS to initialize MongoDB.

In order to stop execution of both containers, go to project root and execute:

.. code-block:: bash

    docker-compose stop

************************************
Running physical JASS installation:
************************************
Set 'MONGO_HOST' environment variable to point to mongo host location. See docker-compose.yml for this variable contents.
Start JASS using jass_startup.sh.

===========
Developers:
===========
For people who want to modify JASS.
 1. Start a dev/test instance of MongoDB. Data will be saved inside the instance.

    .. code-block:: bash

        # From project root
        cd mongo-dev
        docker-compose up -d


 2. Execute database initialisation script. This need to be run only once for test and dev environements.

    .. code-block:: bash

        # From project root
        # Export dev configuration path and run initialization script
        python create_db_if_not_exist.py "configs/dev/config.ini"
        python create_db_if_not_exist.py "configs/dev/config.ini"
        docker-compose up
        # Use docker-compose stop to stop mongo containers

 3. Run JASS.

    .. code-block:: bash

        python -m jass.simple_rest

===============
BASIC API USAGE
===============

| The procedure is to create a document, then add/delete annotations associated with the document
| Using curl http://curl.haxx.se/docs/ to call the api.
| For more information about specific commands see developer documentation at :
| http://jass.readthedocs.org/en/latest/jass.html#module-jass.simple_rest

---------
DOCUMENTS
---------
*************************
Creating a basic document
*************************

.. code-block:: bash

	curl -X POST -H "Content-Type: application/json" -d '{"@context":"test","a":"a","b":"b"}' http://127.0.0.1:5000/document

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