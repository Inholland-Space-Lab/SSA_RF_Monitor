import configparser
import os
import logging

logger = logging.getLogger(__name__)


class Config():
    configFolder = "config/"
    currentConfig = ""
    version = '1'
    __config = configparser.ConfigParser()
    __default = configparser.ConfigParser()

    def start():
        logger.debug('starting config')
        Config.__createDefault()
        Config.open()

    def open(name="default.ini"):
        logger.debug('opening ' + name)
        Config.save()
        Config.currentConfig = name
        path = Config.configFolder + name
        if os.path.exists(path):
            logger.info('opening config ' + name)
            Config.__config.read(path)
            version = ''
            if Config.__config.has_section('Metadata'):
                version = Config.__config['Metadata']['Version']
            if not (version == Config.version):
                logger.warn(
                    "Config %s is outdated! Version is %s instead of required %s", name, version, Config.version)
                Config.__loadDefault()
        else:
            logger.info('no config exists, opening default')
            Config.__loadDefault()
            Config.save()

    def save():
        if Config.currentConfig == "":
            logger.debug("Attempting to save default config")
            return
        logger.info("Saving config: " + Config.currentConfig)

        path = Config.configFolder + Config.currentConfig
        if os.path.exists(path):
            logger.debug('removing old config')
            os.remove(path)

        logger.debug('writing new config')
        with open(path, 'w') as configfile:
            Config.__config.write(configfile)

    def getWebPort() -> int:
        logger.debug('getting web port')
        return Config.__getint('WebConfig', 'port')

    def __createDefault():
        logger.debug('loading default')
        Config.__default = configparser.ConfigParser()
        Config.__default['Metadata'] = {'version': Config.version}
        Config.__default['WebConfig'] = {'port': '8080',
                                         'address': ''}
        logger.debug(Config.__default)

    def __loadDefault():
        Config.__config = Config.__default
        Config.currentConfig = 'default.ini'

    def __getint(section, name) -> int:
        logger.debug("getting value %s from config %s",
                     name, Config.currentConfig)
        default = Config.__default[section].getint(name)
        if Config.__config.has_section(section):
            return Config.__config[section].getint(name, fallback=default)
        else:
            return default
