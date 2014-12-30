#!/usr/bin/env python
# Copyright (C) 2014 CentecNetworks, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# @author: Yi Zhao, Centec Networks, Inc.

import logging
import os

LOG = logging.getLogger(__name__)


class CentecDaemon(object):
    """
    Centec daemon
    """
    def __init__(self, pidfile, procname):
        self.pidfile = pidfile
        self.procname = procname

    def __str__(self):
        return self.pidfile

    def read(self):
        """
        Read pid file
        """
        try:
            fd = os.open(self.pidfile, os.O_RDONLY)
            pid = int(os.read(fd, 128))
            os.lseek(fd, 0, os.SEEK_SET)
            os.close(fd)
            return pid
        except Exception as e:
            LOG.error(("read pid file error."
                       "Exception: %(exception)s"), {'exception': e})
            return

    def is_running(self):
        """
        Check if process is running
        """
        pid = self.read()
        if not pid:
            return False

        cmdline = '/proc/%s/cmdline' % pid
        try:
            with open(cmdline, "r") as f:
                exec_out = f.readline()
            return self.procname in exec_out
        except Exception as e:
            LOG.error(("read %(cmdline)s error."
                       "Exception: %(exception)s"), {'cmdline': cmdline, 'pid': pid, 'exception': e})
            return False
