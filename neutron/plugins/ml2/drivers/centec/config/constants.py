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
# @author: Yi Zhao Centec Networks, Inc.


class CentecConstant(object):

    # default json rpc port number
    JSON_RPC_PORT = 16889
    # agent type linuxbridge
    AGENT_TYPE_LINUXBRIDGE = 'Linux bridge agent'
    # agent type dvr
    AGENT_TYPE_DVR = "Dvr vSwitch agent"
    # supported network typs
    SUPPORTED_NETWORK_TYPES = []


class CentecRpcType(object):

    RPC_TYPE_JSON_OVER_TCP = 0
