#!/usr/bin/env python
# coding:utf-8

"""
Custom logging module.
"""

import logging
import traceback

def logError(genException):
    """
    This function will take an object of the type GenericException and log it
    as an error.
    """
    str_error = "{0} {1} {2}".format(genException.code,
                                     genException.context,
                                     genException)
    logger = logging.getLogger(__name__)                                     
    logger.error(str_error)


def logInfo(genException):
    """
    This function will take an object of the type GenericException and log it
    as information useful for non critical errors.
    """
    str_error = "{0} {1} {2}".format(genException.code, genException.context,
                                     genException)
    logger = logging.getLogger(__name__)                                     
    logger.info(str_error)


def logUnknownError(context, msg, e):
    """
    This function will log all non custom exceptions

    :param msg: Custom error message to put
    :param context: The context to categorize the message
    :param e: Exception object
    """

    # TODO : Look into this standard library function:
    # https://docs.python.org/2.6/library/logging.html#logging.Logger.exception
    # which does essentially the same thing.
    if msg:
        msg += "\n"
    msg = '{0}{1}\n{2}'.format(msg, e, traceback.format_exc())
    str_error = "{0} {1} {2}".format(-1, context, msg)
    # str = ("%i %s %s" %  (-1, context, e))
    logger = logging.getLogger(__name__)                                     
    logger.error(str_error)


def logUnknownWarning(context, msg):
    """
    A simple function to display a warning into logs

    :param msg: Custom error message to put
    :param context: The context to categorize the message
    """
    str_error = "{0} {1} {2}".format(-2, context, msg)
    logger = logging.getLogger(__name__)                                     
    logger.warning(str_error)


def logUnknownInfo(context, msg):
    """
    A simple function to display a info into logs

    :param msg: Custom error message to put
    :param context: The context to categorize the message
    """
    str_error = "{0} {1} {2}".format(-3, context, msg)
    logger = logging.getLogger(__name__)                                     
    logger.info(str_error)
    
def logUnknownDebug(context, msg):
    """
    A simple function to display a debug into logs

    :param msg: Custom error message to put
    :param context: The context to categorize the message
    """
    str_error = "{0} {1} {2}".format(-3, context, msg)
    logger = logging.getLogger(__name__)
    logger.debug(str_error)
