#!/usr/bin/env python
# coding:utf-8

import http.client
from . import settings
import configparser


class Error:
    # Enum of error type
    # (Don't forget to update the __error_code_dict in __init__)
    NO_ERROR = 0
    UNKNOWN = -1
    NOT_INITIALIZED = -2
    URL_NOT_VALID = -3
    FILE_NOT_FOUND = -4
    DB_WRITING_ERROR = -5
    DB_READING_ERROR = -6
    BAD_SERVICE_CONFIGURATION = -7
    SERVICE_NOT_FOUND = -8
    UNKNOWN_UUID = -9
    ANNOTATION_SOURCE_NOT_VALID = -10
    MISSING_PARAMETER = -11

    def __init__(self):
        self.error_code = self.NOT_INITIALIZED
        self.__details = None
        self.__error_code_dict = dict()

        # Dict mapping error codes to an html status code and a msg id tuple
        self.__error_code_dict[self.NO_ERROR] = \
            (http.client.OK, 'NO_ERROR')
        self.__error_code_dict[self.UNKNOWN] = \
            (http.client.INTERNAL_SERVER_ERROR, 'UNKNOWN')
        self.__error_code_dict[self.NOT_INITIALIZED] = \
            (http.client.INTERNAL_SERVER_ERROR, 'NOT_INITIALIZED')
        self.__error_code_dict[self.URL_NOT_VALID] = \
            (http.client.BAD_REQUEST, 'URL_NOT_VALID')
        self.__error_code_dict[self.FILE_NOT_FOUND] = \
            (http.client.NOT_FOUND, 'FILE_NOT_FOUND')
        self.__error_code_dict[self.DB_WRITING_ERROR] = \
            (http.client.INTERNAL_SERVER_ERROR, 'DB_WRITING_ERROR')
        self.__error_code_dict[self.DB_READING_ERROR] = \
            (http.client.INTERNAL_SERVER_ERROR, 'DB_READING_ERROR')
        self.__error_code_dict[self.BAD_SERVICE_CONFIGURATION] = \
            (http.client.INTERNAL_SERVER_ERROR, 'BAD_SERVICE_CONFIGURATION')
        self.__error_code_dict[self.SERVICE_NOT_FOUND] = \
            (http.client.BAD_REQUEST, 'SERVICE_NOT_FOUND')
        self.__error_code_dict[self.UNKNOWN_UUID] = \
            (http.client.BAD_REQUEST, 'UNKNOWN_UUID')
        self.__error_code_dict[self.ANNOTATION_SOURCE_NOT_VALID] = \
            (http.client.BAD_REQUEST, 'ANNOTATION_SOURCE_NOT_VALID')
        self.__error_code_dict[self.MISSING_PARAMETER] = \
            (http.client.BAD_REQUEST, 'MISSING_PARAMETER')

    def is_ok(self):
        return self.error_code == self.NO_ERROR

    def set_error(self, code):
        self.error_code = code
        self.__details = None

    def set_error_with_details(self, code, **kwargs):
        self.error_code = code
        self.__details = kwargs

    def get_html_status(self):
        return self.__error_code_dict[self.error_code][0]

    @staticmethod
    def get_html_status_msg_from_status(status):
        return http.client.responses[status]

    def get_html_status_msg(self):
        return Error.get_html_status_msg_from_status(self.get_html_status())

    def get_message(self):
        msg_id = self.__error_code_dict[self.error_code][1]
        if self.__details:
            try:
                msg = settings.GetConfigValue('canarie_status_msg_details',
                                              msg_id)
                msg = msg.format(**self.__details)
                return msg
            except configparser.Error:
                pass

        return settings.GetConfigValue('canarie_status_msg', msg_id)
