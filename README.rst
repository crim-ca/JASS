============================================
NEP-143-1 Annotation Storage Service
============================================

The purpose of this JSON Annotation Storage Service (JASS) is to offer a
REST API to store and manipulate large amounts of JSON annotations. Annotation are stored in a
MongoDB backend.

---------------------
Overview
---------------------

There are 3 elements which are stored in the annotation storage:

- Documents. A document contains multiple annotations.
- Annotations. An annotation describes the document it is contained in. (An
  annotation cannot exist by itself)
- Schema. Used to describe the structure of an annotation. Schemas are not enforced.

Note that due to the choice of the storage back end the JSON content of a
Document, Annotation or Schema can not exceed 16 MB in size.
