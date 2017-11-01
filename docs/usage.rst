Usage
=====

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

**Creating one batch** containing multiple annotations

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

------------------------
Global Annotation Search
------------------------
When having to search for manual annotations across all documents or some documents, there is a global search endpoint.

To support pagination needs, there are optional skip and limit fields to respectively skip a number of search results and limit the number of search results.

If a text search is used (see below), the results are returned in descending order of relevance score.

This example skips no results and limits to 2 results returned.

.. code-block:: bash

	curl --request POST \
	  --url http://127.0.0.1:5000/annotations/search \
	  --header 'content-type: application/json' \
	  --data '{
		"query": {
			"annotationTypeId": "transcription"
		},
		"skip": 0,
		"limit": 2
	}'

--------------------------------
Global Grouped Annotation Search
--------------------------------
Search manual annotations (storageType 1) and group them by timeline.

Returns the text index fields and an array of annotation matches grouped by timeline (annotationSetId).

Each match contains the annotation and score matching the query, sorted descending by score.

Groups are also sorted descending by score. Group scores are the sum of its match scores.

Group searched must contain a $text query.

*Efficiency consideration*

AFAIK MongoDB isn't really as efficient on aggregate operations as a standard relational database would be. Same goes for sorting on the score. As such, we can expect searches with a large number of results to be slow.

Searches known to match a significant proportion of a large number of annotations should be avoided. E.G searching for *male* or *female* knowing one of the text index field will contain only one or the other. These kind of specialized, domain specific queries would be better served with a normal, non-text search, on a single document.

Grouped search have the same API as the global search:

.. code-block:: bash

	curl --request POST \
	  --url http://ss-vl-vesta04.crim.ca:9880/annotations/grouped-search \
	  --header 'content-type: application/json' \
	  --data '{
		"query": {
			"$text": {
				"$search": "java coffee shop"
			},
			"doc_id": {
				"$in": [
					"584f1836d2b2b60082a71576",
					"555f30591747d5574b3900af",
					"556884621747d5574b3cd591"
				]
			}
		},
		"skip": 0,
		"limit": 5
	}'

----------------------
Annotation Text Search
----------------------
Whether using *jsonSelect* on a single document or doing a global *query* across documents, it is possible to do a text search.
For details, see MongoDB Documentation https://docs.mongodb.com/manual/text-search/

Note: the JASS has been configured for the text search need of the VESTA platform. As such, the text index is comprised of the following fields:
- text
- motionName
- shotName
- speakerId
- speakerSubtype

Text search will only search those fields for the given search expression.

A small example using global search

.. code-block:: bash

	curl --request POST \
	  --url http://127.0.0.1:5000/annotations/search \
	  --header 'content-type: application/json' \
	  --data '{
		"query": {
			"$text": {
				"$search": "java coffee shop"
			}
		},
		"skip": 0,
		"limit": 2
	}'


Note: by default, rules for indexing and searching text is done using English. A different language can be specified while storing an annotation and when searching. For best results, the same language should be used when indexing and searching.

Storing a annotation with French fields:

.. code-block:: bash

	curl -v -H "Content-Type: application/json" -H "Accept: application/json" -d \
	    '{"text": "cheval", "language": "french"}' http://127.0.0.1:5000/document/<document_id>/annotation


Searching annotations with French fields:

.. code-block:: bash

	curl --request POST \
	  --url http://127.0.0.1:5000/annotations/search \
	  --header 'content-type: application/json' \
	  --data '{
		"query": {
			"$text": {
				"$search": "chevaux",
				"$language": "french"
			}
		}
	}'