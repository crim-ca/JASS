#!/usr/bin/env python
# coding:utf-8

"""
This module is a collection of utility functions used by the rest_route module
placed here to keep the rest_route module as clear as possible.
"""


# -- Standard lib ------------------------------------------------------------
import re
import sqlite3
import os
import datetime
import logging
import http.client

# -- 3rd party ---------------------------------------------------------------
from flask import request
from flask import render_template
from flask import jsonify
from flask import Response
from flask import g
from flask import redirect
from flask import make_response
from flask import Markup
from flask import current_app
import pytz


# -- Project specific --------------------------------------------------------
import settings
import error


class UnknownServiceError(Exception):
    """Service name is of unknown type"""
    pass


# ----------------------------------------------------------------------------
def request_wants_json():
    """
    Check if the request type is JSON

       Deals with */*
    """
    best = request.accept_mimetypes.best_match(['application/json',
                                                'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def get_canarie_api_response(service_name ,template_path,canarie_api_request):
    """
    Provide a valid HTML response for the CANARIE API request based on the
    service_route.

    :param:
        :service_route: Route name of the service coming from the URL e.g.:
                       ['diarisation', 'STT', etc.]
                       
        :canarie_api_request: The request specified in the URL
    :returns: A valid html response
    """

    # The service configuration should return either :
    #      - A valid URL (in which case a redirection is performed)
    #      - A relative template file from which an html page is rendered
    #      - A comma separated list corresponding to the response tuple
    #      (response, status)
    cfg_val = settings.GetConfigValue(service_name,canarie_api_request)
    if cfg_val.find('http') == 0:
        return redirect(cfg_val)

    elif os.path.isfile(os.path.join(template_path,
                                     cfg_val)):
        return render_template(cfg_val)

    elif len(cfg_val.split(',')) == 2:
        return make_response(*(cfg_val.split(',')))

    else:
        return make_error_response(error.Error.BAD_SERVICE_CONFIGURATION)


def get_server_restart_time():
    """
    Obtain the server status provided by Apache if properly configured.
    The configuration file must contain the following section:

    ::
    
        # Enable the module mod_status
        # See : http://httpd.apache.org/docs/2.2/mod/mod_status.html
        <Location /server-status>
            SetHandler server-status
            Order deny,allow
            #Deny access for everyone outside
            Deny from all
            #Allow access from IP 10* (private address inside local network)
            Allow from 10
            #Allow access from 132.217* (public IP range own by the CRIM)
            Allow from 132.217
        </Location>
    
        # Keep track of extended status information for each request
        ExtendedStatus On
    """

    conn = http.client.HTTPConnection(settings.GetConfigValue('Server', 'Name'))
    conn.request("GET", "/server-status")
    response = conn.getresponse()
    if response.status == http.HTTPStatus.OK:
        body = response.read()
        restart_time_match = re.search('<dt>Restart Time: [a-zA-Z]*, '
                                       '([^ ]* [0-9:]{8}) (.*)</dt>',
                                       body)
        if restart_time_match:
            datetime_str = restart_time_match.group(1)
            timezone_str = restart_time_match.group(2)

            # EDT is not in the pytz package so use this time zone
            # which gives the correct +4hours offset to the UTC
            timezone_str = re.sub('EDT', 'Etc/GMT+4', timezone_str)

            local = pytz.timezone(timezone_str)
            localtime_unaware = datetime.datetime.strptime(datetime_str,
                                                           '%d-%b-%Y %H:%M:%S')
            local_time = local.localize(localtime_unaware, is_dst=None)
            utc_time = local_time.astimezone(pytz.utc)

            return utc_time

    logging.error("Failed to retrieve restart time of server {0}".
                  format(settings.GetConfigValue('Server', 'Name')))
    return None


# ---------------------------------------------------------------------------
def handle_error(more_info, status):
    """
    Creates a standardized error response.
    """
    message = error.Error.get_html_status_msg_from_status(status)
    match = re.search("^([0-9]*):? *(.*)$", more_info)
    if match:
        error_code = match.group(1)
        if error_code == str(status):
            # The more_info already contains the error code, use it as message
            # and clear more_info (which didn't provide additional information)
            message = match.group(2)
            more_info = ''

    return error_response(status, message, error.Error.UNKNOWN, more_info)


def make_error_response(error_code):
    """
    Create an error response from a single error code.
    """
    error_obj = error.Error()
    error_obj.set_error(error_code)
    return error_response(error_obj.get_html_status(),
                          error_obj.get_html_status_msg(),
                          error_obj.error_code,
                          error_obj.get_message())


def make_error_response_with_details(error_code, **kwargs):
    """
    Create an error response from a single error code.
    """
    error_obj = error.Error()
    error_obj.set_error_with_details(error_code, **kwargs)
    return error_response(error_obj.get_html_status(),
                          error_obj.get_html_status_msg(),
                          error_obj.error_code,
                          error_obj.get_message())


def error_response(status, message, code, more_info):
    """
    Format error according to request type.
    """
    # TODO: All REST requests call this function in case of error/exception.
    # So if some logging is required, a generic error message is to be shown
    # or something else must be done. It should be done here rather than
    # everywhere else.

    # TODO: To enable sending a mail on error, this page could be useful:
    # flask.pocoo.org/docs/errorhandling

    full_status_msg = str(status) + ": " + message
    full_info_msg = str(code) + ": " + more_info

    logging.error("Application error occurs : {0}".format(full_info_msg))
    logging.error("Send html response : {0}".format(full_status_msg))

    if request.accept_mimetypes['text/html']:
        if not more_info:
            return render_template('error.html', Error=full_status_msg), status
        else:
            # Make break line more readable in html
            if full_info_msg.find("\\n"):
                # Start by escaping already present html symbols
                full_info_msg = (full_info_msg.replace("&", "&amp;")
                                 .replace("<", "&lt;")
                                 .replace(">", "&gt;")
                                 .replace("'", "&#39;")
                                 .replace('"', "&quot;"))
                # Then replace break line by the <br> symbol
                full_info_msg = full_info_msg.replace("\\n", "<br>")
                # And mark the string as a markup string
                full_info_msg = Markup(full_info_msg)

            return render_template('error.html',
                                   Error=full_status_msg,
                                   Details=full_info_msg), status
    elif not request_wants_json():
        # Line break doesn't make sense in a XML
        more_info = more_info.replace("\\n", " ")
        return Response(response=render_template('error.xml',
                                                 Status=status,
                                                 Message=message,
                                                 Code=code,
                                                 More_info=more_info),
                        status=status,
                        mimetype="application/xml")
    else:
        if not more_info:
            response = {'Status': status, 'Message': message}
        else:
            # Line break doesn't make sense in JSON
            more_info = more_info.replace("\\n", " ")
            response = {'Status': status,
                        'Message': message,
                        'Code': code,
                        'More_info': more_info}
        return jsonify(response), status
