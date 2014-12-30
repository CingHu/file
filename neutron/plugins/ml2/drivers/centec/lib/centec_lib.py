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


class CentecLib(object):

    @staticmethod
    def ipv4_to_int(string):
        if isinstance(string, basestring):
            pass
        elif isinstance(string, int):
            return string
        elif isinstance(string, long):
            return string

        try:
            ip = string.split('.')
            if len(ip) != 4:
                raise ValueError('Invalid format for IPv4 address: %s' % string)
            i = 0
            for b in ip:
                b = int(b, 10)
                if b < 0 or b > 255:
                    raise ValueError('Invalid format for IPv4 address: %s' % string)
                i = (i << 8) | b
        except:
            raise ValueError('Invalid format for IPv4 address: %s' % string)
        return i

    @staticmethod
    def any_to_int(value, base):
        """
        Convert any format to integer
        :param value: value
        :param base: base
        """
        if not isinstance(value, int):
            try:
                value = int(str(value), base)
            except ValueError:
                return 0
        return value
