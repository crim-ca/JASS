#!/usr/bin/env python
# coding:utf-8

import re


class GenericException(Exception):
    context = "GenericException"
    code = 0

    @staticmethod
    def __CustomFormat(template, *args, **kwargs):
        next_index = len(args)
        while True:
            try:
                return template.format(*args, **kwargs)
            except KeyError as e:
                key = e.args[0]
                finder = '\{' + key + '.*?\}'
                template = re.sub(finder, '{\g<0>}', template)
            except IndexError as e:
                args = args + ('{' + str(next_index) + '}',)
                next_index += 1

    def __init__(self, code, *args):
        """
        Creates a message and populates it with parameters.
        If it can not find a code, or the number of arguments is wrong, it will
        generate a default message.

        :param code: Error code
        :param messageParams: An Array Containing additional message
                              parameters.
        """
        message = ""
        self.code = code
        if (not args):
            try:
                message = self.codeToMessage[code]
            except Exception:
                message = "Message not could not be formatted for code: {0}".\
                          format(code)
        else:
            try:
                message = GenericException.__CustomFormat(
                    self.codeToMessage[code], *args)
            except Exception:
                message = "Message not could not be formatted for code: %{0}\n"\
                          " params: {1}".\
                          format(code, ', '.join([str(x) for x in args]))
        self.msg = message
        super(GenericException, self).__init__(self)

    # http://stackoverflow.com/questions/1272138/baseexception-message-deprecated-in-python-2-6
    def __str__(self):
        return repr(self.msg)
