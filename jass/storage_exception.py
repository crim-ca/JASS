from .generic_exception import GenericException


class MongoDocumentException(GenericException):
    """
    Exceptions occurring when Manipulating an object in MongoDB,
    """
    codeToMessage = {0: "Unexpected Exception",
                     2: "Storage document should not be empty.",
                     3: "Storage document is missing the required @context "
                        "field",
                     4: "Storage document contains a reserved field : {0}",
                     5: "Storage Document with id : {0} not found for update"}
    context = "Annotation Storage Document"


class AnnotationException(GenericException):
    """
    Exceptions when manipulating Annotations
    """
    codeToMessage = {0: "Unexpected Exception",
                     1: "Invalid document object Id {0}",
                     2: "Annotation: {0} in batch is missing a context for doc"
                        " {1}",
                     3: "Invalid document id detected: {0}, operation "
                        "aborted.",
                     4: "Annotation: {0} in batch is missing a required field"
                        " for doc {1}",
                     5: "Format {0} is not supported",
                     6: "StorageType: {0} is not initialized ",
                     7: "StorageType: {0} is not supported ",
                     8: "Number of inserted annotations is not equal to the "
                        "number of annotations in batch: {0} vs {1}",
                     9: "Some of the document IDs have invalid format."
                     }
    context = "Annotation Storage Annotation"


class StorageException(GenericException):
    """
    Exceptions related to the functionality of the MongoDB database itself
    """
    context = "Annotation Storage Storage"
    codeToMessage = {1: "Failed to connect to MongoDB",
                     2: "Unexpected delete fail to MongoDB"}


class StorageRestExceptions(GenericException):
    """
    Exception related to the rest part of the program
    """
    codeToMessage = {0: "ErrorCode not supported. Please contact administrator"
                        " if you see this error.",
                     1: "Inconsistent document. The id contained in the"
                        " document is not the same as the one called.",
                     2: "Did not found the document requested",
                     3: "Can not update document since the id described does"
                        " not exist.",
                     4: "The id supplied is not located in Human Storage."
                        " This request only works with Human Storage.",
                     5: "One of the supplied request parameters is invalid."}
