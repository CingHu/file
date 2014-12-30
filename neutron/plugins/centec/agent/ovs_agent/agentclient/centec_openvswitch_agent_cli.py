#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs bridge agent start up
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import sys
from neutron.plugins.centec.agent.ovs_agent.agentclient import client

def main():
    sys.exit(client.main())

if __name__ == "__main__":
    main()
