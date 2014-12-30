#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent logger module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

from neutron.openstack.common import log as logging


class Logger(object):
    def __init__(self, module):
        '''
        init
        :param module: module name
        '''
        self._module = module
        self._console = None
        self._rofile = None
        self._logger = self._get_logger(module)

    def _get_logger(self, module):
        '''
        create a logger
        :param module: logger name
        '''
        logger = logging.getLogger(module)
        return logger

    # log level
    def debug(self, msg):
        self._logger.debug(_(msg))

    def info(self, msg):
        self._logger.info(_(msg))

    def warn(self, msg):
        self._logger.warning(_(msg))

    def error(self, msg):
        self._logger.error(_(msg))
