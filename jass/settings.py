#!/usr/bin/env python
# coding:utf-8

"""
General settings for the REST API
"""

# --Standard lib module---------------------------------------
import os
import configparser

# --Project specific------------------------------------------
import singleton
import custom_logger as logger
from generic_exception import GenericException
from singleton import Singleton
import os


class SettingsExceptions(GenericException):
    """
    Custom exceptions for settings
    """
    codeToMessage = {1: 'Cannot load settings because the configuration file '
                        'is not found : {0}.',
                     3: 'Cannot load settings because the configuration file'
                        ' ({0}) loads an invalid services configuration file'
                        ' : {1}. Services configuration file must contains'
                        ' only one section being the service name.'
                     }


@singleton.Singleton
class Settings(Singleton):
    """
    The settings should respect the following structure:
    a path to the init file containing the settings.
    """

    def __init__(self):
        self.__config = None
        self.__config_path = None

    def LoadConfig(self, config_path):
        """
        Set the config path and loads configuration
        @param config_path: Set the config path and loads the configuration
        """
        self.__config_path = config_path
        self.__load_settings(config_path)

    def GetConfigValue(self, namespace, key):
        """
        Generic accessor for configuration values

        :param namespace: Section of the INI
        :param key: Actual key for which we want a value. if key exists as an environement variable,
            it will use environement variable instead
        """
        return self.__config.get(namespace, key)

    def __load_settings(self, config_path):
        """
        load setting specified by config path
        """

        self.__config = None

        if not os.path.exists(config_path):
            exc = SettingsExceptions(1, config_path)
            logger.logError(exc)
            raise exc

        self.__config = configparser.ConfigParser()
        self.__config.read(config_path)


def GetConfigValue(namespace, key):
    """
    Generic accessor for configuration values

    :param namespace: Section of the INI
    :param key: Actual key for which we want a value.
    """
    if key in os.environ:
        return os.environ[key]
    else:
        return Settings.Instance().GetConfigValue(namespace, key)
