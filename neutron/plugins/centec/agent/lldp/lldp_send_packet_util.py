#!/usr/bin/python
'''
Created on Jun 20, 2013

@author: Alexandru Nicolae
'''

from sys import argv
from neutron.plugins.centec.agent.lldp.Packet_Generator import *

def main():    
    length = len(argv)
    if length < 3:
        message1()
        exit(0)
    
    packet = None
    interface = None
    
    result = create_packet(argv) #create packet based on CLI informations
    #if the interface is not specified, eth1 is considered default
    if(len(result) == 1):
        packet = result[0]
        interface = "eth1" 
    else:
        packet = result[0]
        interface = result[1]
        print interface
       
    #ans,unans = srp(packet,verbose=1,iface=interface) #send and receive answers
    sendp(packet,verbose=1,iface=interface) #only send
