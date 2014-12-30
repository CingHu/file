#!/usr/bin/python
'''
Created on Jun 8, 2013

@author: Alexandru Nicolae
'''

from scapy.all import *
from sys import exit
import string
import random
import re
from IPy import IP  # this program is used to validate IPv4 and IPv6 addresses
import time

from neutron.plugins.centec.agent.lldp.LLDP_TLV import *
from neutron.plugins.centec.agent.lldp.NotificationBox import *
 
# Random MAC generator for PortID and Chassis ID addresses
'''Usually, Port ID value is a MAC address equal to sender's MAC address and Chassis ID
value is also a MAC address equal to Port ID value, but with the last octet containing
only zeros'''
def RandMac():
    mac = [ 0x30, 0x85, 0xa9,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    result = []
    port_id = map(lambda y: "%02x" % y, mac)
    port_id = ":".join(port_id)
    
    mac[5] = 0x00
    chid = map(lambda y: "%02x" % y, mac)
    chid = ":".join(chid)
    
    result.append(chid)
    result.append(port_id)
    return result

# This function's scope is to create a LLDP frame based on CLI commands
def create_packet(argv):
    frame = Ether()
    frame.dst = '01:80:c2:00:00:0e'  # LLDP multicast address
    rand_mac = RandMac()
    frame.src = rand_mac[1]  # the frame's source is equal with the Port ID value
    frame.type = 0x88cc  # LLDP ethertype
    
    packet = frame
    chid = None
    portid = None
    ttl = None
    interface = None
    port_desc = sys_name = sys_desc = sys_cap = mgm_add = port_vid = pp_vid = vlan_name = prot_id \
 = vid_digest = mgm_vid = link_agg1 = link_agg3 = mac_phy = power = max_frame = None
    
    length = len(argv)
    result = []  # two elements list: [packet,out_interface]
    mandatories = []  # mandatory TLVs list: chid, portid,ttl [endpdu]
    optionals = []  # optionals TLVs
    tlvs = []

    i = 3
    #print argv[0]
    #print argv[1]
    if(argv[1] == '-p'):
        if(argv[2] == 'lldp' or argv[2] == 'LLDP'):
            if(length == 3):  # Case1: command is: tool -p lldp 
                chid = Chassis_ID()
                chid.macaddr = rand_mac[0]
                portid = Port_ID()
                portid.macaddr = rand_mac[1]
                ttl = TTL()
                ttl.seconds = 30
                
                #print "Port ID - simple frame"
                #print portid.macaddr
                
                end_pdu = EndOfPDU()
                
                packet /= chid / portid / ttl / end_pdu
                result.insert(0, packet)
                
                return result  # create a base LLDP frame containing only mandatory TLVs
                
            elif(argv[3] == '-i' and len(argv) <= 5):  # Case2: commands is: tool -p lldp -i [interface]
                if (length == 4):
                    print "Wrong syntax, should be: tool -p lldp [ -i eth1|lo]\n"
                    exit(0)
                # Comment out by zhangdy to allow any interface to be used for sending
                # lldp packet.
                #elif (argv[4] != 'eth1' and argv[4] != 'lo'):  # only eth1 and lo0 available for me
                #    print "tool -p lldp [ -i eth1|lo]\n"
                #    exit(0)
                #    
                else:
                    interface = argv[4]
                    chid = Chassis_ID()
                    chid.macaddr = rand_mac[0]
                    portid = Port_ID()
                    portid.macaddr = rand_mac[1]
                    ttl = TTL()
                    ttl.seconds = 30
                    
                    #print "Port ID - simple frame "
                    #print portid.macaddr
                    
                    end_pdu = EndOfPDU()
                
                    packet /= chid / portid / ttl / end_pdu
                    
                    result.insert(0, packet)
                    result.append(interface)
                    return result  # create a base LLDP frame with the output interface specified
                    
                  
            while(True):  # Case3: creation of complex frames(multiple TLVs)
                    if(i == length):  # if one mandatory TLV is missing, it is randomly created
                        if(chid != None):
                            mandatories.insert(0, chid)
                        else:
                            chid = Chassis_ID()
                            chid.macaddr = rand_mac[0]
                            mandatories.insert(0, chid)
                            
                        if(portid != None):
                            mandatories.insert(1, portid)
                        else:
                            portid = Port_ID()
                            portid.macaddr = rand_mac[1]
                            mandatories.insert(1, portid)
                            
                        if(ttl != None):
                            mandatories.append(ttl)  
                        else:
                            ttl = TTL()
                            ttl.seconds = 30
                            mandatories.append(ttl)  
                        
                        #print "Port ID - complex frame "
                        #print portid.macaddr
                        
                        # Creation of a LLDPDU
                        tlvs = mandatories + optionals
                        end_pdu = EndOfPDU()
                        tlvs.append(end_pdu)
                        tlvs.insert(0, frame) 
                        # Creation of a LLDP frame
                        packet = tlvs[0]
                        for cnt in range (1, len(tlvs)):
                            packet /= tlvs[cnt]
                        
                        result.insert(0, packet)
                        break
                            
                    if(argv[i] == '-i'):
                        if (i >= length - 1):  # case: -tlv 'type' 'subtype' value -i [nothing]
                            print "tool -p lldp [ -i eth1|lo] -tlv 'type' [-subtype] 'value'\n"
                            exit(0)
                            
                        interface = argv[i + 1]
                        # Comment out by zhangdy for allowing send packet using any interface.
                        #
                        #if(interface != 'eth1' and interface != 'lo'):  # only eth1 and lo0 available for me
                        #    print "tool -p lldp [ -i eth1|lo] -tlv 'type' [-subtype] 'value'\n"
                        #    exit(0)
                        #else:     
                        result.append(interface)
                        i += 2
                        continue
                        
                    # The second condition is there to make sure that at least one argument is in arguments list
                    if((argv[i] == '-tlv' or argv[i] == 'TLV') and i < length - 1): 
                        # If the next argument is chid and it's the first time it is introduced 
                        if((argv[i + 1] == 'chid' or argv[i + 1] == 'CHID') and chid == None):
                            if (i + 3 > length - 1):  # make sure that I have two parameters after 'chid'
                                chid_ussage()
                                exit(0)
                            else:
                                chid = Chassis_ID()
                                chid.type = 0x01
                                
                                # analyzing Chassis ID subtypes
                                
                                if(argv[i + 2] == '-chassis-comp'):
                                    chid.subtype = 0x01
                                    chid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        chid_ussage()
                                        exit(0)
                                    chid.chassisComponent = value
                                    chid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                
                                if(argv[i + 2] == '-int-alias'):
                                    chid.subtype = 0x02
                                    chid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        chid_ussage()
                                        exit(0)
                                        
                                    chid.interfaceAlias = value
                                    chid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-port-comp'):
                                    chid.subtype = 0x03
                                    chid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        chid_ussage()
                                        exit(0)
                                        
                                    chid.portComponent = value
                                    chid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-mac-addr'):
                                    chid.subtype = 0x04
                                    chid.length = 7
                                    chid.addrType = 0x00
                                    value = argv[i + 3]
                                    
                                    if (re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", value.lower()) == None):
                                        chid_ussage()
                                        exit(0)
                                    chid.macaddr = value
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-ipv4'):
                                    chid.subtype = 0x05
                                    chid.addrType = 0x01
                                    value = argv[i + 3]
                                    
                                    val = True
                                    try:
                                        IP(value)
                                    except:
                                        val = False
                                    if(val == False):
                                        chid_ussage()
                                        exit(0)
                                    chid.ipaddr = value
                                    chid.length = 1 + 1 + 4  # subtype,addrType, ip addr
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-ipv6'):
                                    chid.subtype = 0x05
                                    chid.addrType = 0x02
                                    value = argv[i + 3]
                                    
                                    val = True
                                    try:
                                        IPv6(value)
                                    except:
                                        val = False
                                    if(val == False):
                                        chid_ussage()
                                        exit(0)
                                        
                                    chid.ip6addr = value
                                    chid.length = 1 + 1 + 16
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-int-name'):
                                    chid.subtype = 0x06
                                    chid.addrType = 0x00
                                    value = argv[i + 3]
                                    
                                    if(len(value) < 1 or len(value) > 255):
                                        chid_ussage()
                                        exit(0)
                                        
                                    chid.interfaceName = value
                                    chid.length = len(value) + 1  # value + subtype
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-local'):
                                    chid.subtype = 0x07
                                    chid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        chid_ussage()
                                        exit(0)
                                        
                                    chid.locallyAssigned = value
                                    chid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                 
                                else:
                                    chid = None
                                    chid_ussage()
                                    exit(0)
                        
                        if((argv[i + 1] == 'chid' or argv[i + 1] == 'CHID') and chid != None):
                            print "Chassis ID is already set\n"
                            exit(0)
                        
                        
                        
                        
                        
                        # Almost the same as Chassis ID
                        if((argv[i + 1] == 'port-id' or argv[i + 1] == 'PORT-ID') and portid == None):
                            if (i + 3 > length - 1):  # make sure I have two parameters after 'port-id'
                                portid_ussage()
                                exit(0)
                            else:
                                portid = Port_ID()
                                portid.type = 0x02
                                
                                if(argv[i + 2] == '-int-alias'):
                                    portid.subtype = 0x01
                                    portid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        portid_ussage()
                                        exit(0)
                                        
                                    portid.interfaceAlias = value
                                    portid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-port-comp'):
                                    portid.subtype = 0x02
                                    portid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        portid_ussage()
                                        exit(0)
                                        
                                    portid.portComponent = value
                                    portid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-mac-addr'):
                                    portid.subtype = 0x03
                                    portid.length = 7
                                    portid.addrType = 0x00
                                    value = argv[i + 3]
                                    
                                    if (re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", value.lower()) == None):
                                        portid_ussage()
                                        exit(0)
                                    portid.macaddr = value
                                    i = i + 4
                                    packet.src = portid.macaddr # modified by Centec 
                                    continue
                                    
                                if(argv[i + 2] == '-ipv4'):
                                    portid.subtype = 0x04
                                    portid.addrType = 0x01
                                    value = argv[i + 3]
                                    
                                    val = True
                                    try:
                                        IP(value)
                                    except:
                                        val = False
                                    if(val == False):
                                        portid_ussage()
                                        exit(0)
                                    portid.ipaddr = value
                                    portid.length = 1 + 1 + 4  # subtype,addrType, ip addr
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-ipv6'):
                                    portid.subtype = 0x04
                                    portid.addrType = 0x02
                                    value = argv[i + 3]
                                    
                                    val = True
                                    try:
                                        IPv6(value)
                                    except:
                                        val = False
                                    if(val == False):
                                        portid_ussage()
                                        exit(0)
                                        
                                    portid.ip6addr = value
                                    portid.length = 1 + 1 + 16
                                    i = i + 4
                                    continue
                                    
                                if(argv[i + 2] == '-int-name'):
                                    portid.subtype = 0x05
                                    portid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        portid_ussage()
                                        exit(0)
                                        
                                    portid.interfaceName = value
                                    portid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                
                                if(argv[i + 2] == '-agent-id'):
                                    portid.subtype = 0x06
                                    portid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        portid_ussage()
                                        exit(0)
                                        
                                    portid.agentCircutID = value
                                    portid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                   
                                if(argv[i + 2] == '-local'):
                                    portid.subtype = 0x07
                                    portid.addrType = 0x00
                                    value = argv[i + 3]
                                    if(len(value) < 1 or len(value) > 255):
                                        portid_ussage()
                                        exit(0)
                                        
                                    portid.locallyAssigned = value
                                    portid.length = len(value) + 1
                                    
                                    i = i + 4
                                    continue
                                
                                else:
                                    portid = None
                                    portid_ussage()
                                    exit(0)
                        
                        if((argv[i + 1] == 'port-id' or argv[i + 1] == 'PORT-ID') and portid != None):
                            print "Port ID is already set\n"
                            exit(0)
                            
                        if((argv[i + 1] == 'ttl' or argv[i + 1] == 'TTL') and ttl == None):
                            
                            if(i + 2 > length - 1):
                                ttl_ussage()
                                exit(0)
                                
                            value = int(argv[i + 2])
                            if(value < 0 or value > 65535):
                                ttl_ussage()
                                exit(0)
                            ttl = TTL()
                            ttl.length = 2
                            ttl.seconds = value
                            i += 3
                            continue
                            
                        if((argv[i + 1] == 'ttl' or argv[i + 1] == 'TTL') and ttl != None):
                            print "TTL is already set\n"
                            exit(0)
                            
                        """Following: OPTIONALS TLVs"""
                        
                        if ((argv[i + 1] == 'port-desc' or argv[i + 1] == 'PORT-DESC') and \
                             port_desc == None):

                            if(i + 2 > length - 1):
                                port_desc_ussage()
                                exit(0)
                            value = argv[i + 2]
                            if(len(value) < 0 or len(value) > 255):
                                ttl_ussage()
                                exit(0)
                            port_desc = PortDescription()
                            port_desc.length = len(value)
                            port_desc.portDescription = value
                            optionals.append(port_desc)
                            i += 3
                            continue
                        
                        if ((argv[i + 1] == 'port-desc' or argv[i + 1] == 'PORT-DESC') and \
                             port_desc != None):
                            print "Port Description is already set"
                            exit(0)
                            
                        if ((argv[i + 1] == 'sys-name' or argv[i + 1] == 'SYS-NAME') and \
                             sys_name == None):
                            if(i + 2 > length - 1):
                                sys_name_ussage()
                                exit(0)
                            value = argv[i + 2]
                            if(len(value) < 0 or len(value) > 255):
                                sys_name_ussage()
                                exit(0)
                            
                            sys_name = SystemName()
                            sys_name.length = len(value)
                            sys_name.systemName = value
                            
                            optionals.append(sys_name)
                            i += 3
                            continue
                        if ((argv[i + 1] == 'sys-name' or argv[i + 1] == 'SYS-NAME') and \
                             sys_name != None):
                            print "System Name is already set"
                            exit(0)
                            
                        if ((argv[i + 1] == 'sys-desc' or argv[i + 1] == 'SYS-DESC') and \
                            sys_desc == None):
                            if(i + 2 > length - 1):
                                sys_desc_ussage()
                                exit(0)
                            value = argv[i + 2]
                            if(len(value) < 0 or len(value) > 255):
                                sys_desc_ussage()
                                exit(0)
                                
                            sys_desc = SystemDescription()
                            sys_desc.length = len(value)
                            sys_desc.systemDescription = value
                            optionals.append(sys_desc)
                            i += 3
                            continue
                        
                        if ((argv[i + 1] == 'sys-desc' or argv[i + 1] == 'SYS-DESC') and \
                            sys_desc != None):
                            print "System description is already set"
                            exit(0)
                            
                        if ((argv[i + 1] == 'sys-cap' or argv[i + 1] == 'SYS-CAP') and \
                            sys_cap == None):
                            
                            if(i + 5 > length - 1):
                                sys_cap_ussage()
                                exit(0)
                                
                            sys_cap = SystemCapabilities()
                            sys_cap.length = 4

                            if(argv[i + 2] == '-system'):
                                value = argv[i + 3]
                                value = value.split(",")  # obtaining list of values
                                sum = 0
                                for k in range(0, len(value)):
                                    if (value[k] == "other"):
                                        sum += 1
                                        continue
                                    if (value[k] == 'repeater'):
                                        sum += 2
                                        continue
                                    if (value[k] == 'bridge'):
                                        sum += 4
                                        continue
                                    if (value[k] == 'ap'):
                                        sum += 8
                                        continue
                                    if (value[k] == 'router'):
                                        sum += 16
                                        continue
                                    if (value[k] == 'phone'):
                                        sum += 32
                                        continue
                                    if (value[k] == 'docsis'):
                                        sum += 64
                                        continue
                                    if (value[k] == 'station'):
                                        sum += 128
                                        continue
                                    if (value[k] == 'cvlan'):
                                        sum += 256
                                        continue
                                    if (value[k] == 'svlan'):
                                        sum += 512
                                        continue
                                    if (value[k] == 'tprelay'):
                                        sum += 1024
                                        continue
                                    else:
                                        sys_cap_ussage()
                                        exit(0)  
                                sys_cap.systemCapabilities = sum
                                
                                if(argv[i + 4] == '-enabled'):
                                    value = argv[i + 5]
                                    value = value.split(",")
                                    sum = 0
                                    for k in range(0, len(value)):
                                        if (value[k] == 'other'):
                                            sum += 1
                                            continue
                                        if (value[k] == 'repeater'):
                                            sum += 2
                                            continue
                                        if (value[k] == 'bridge'):
                                            sum += 4
                                            continue
                                        if (value[k] == 'ap'):
                                            sum += 8
                                            continue
                                        if (value[k] == 'router'):
                                            sum += 16
                                            continue
                                        if (value[k] == 'phone'):
                                            sum += 32
                                            continue
                                        if (value[k] == 'docsis'):
                                            sum += 64
                                            continue
                                        if (value[k] == 'station'):
                                            sum += 128
                                            continue
                                        if (value[k] == 'cvlan'):
                                            sum += 256
                                            continue
                                        if (value[k] == 'svlan'):
                                            sum += 512
                                            continue
                                        if (value[k] == 'tprelay'):
                                            sum += 1024
                                            continue
                                        else:
                                            sys_cap_ussage()
                                            exit(0)  
                                    sys_cap.enabledCapabilities = sum
                                else:
                                    sys_cap_ussage()
                                    exit(0) 
                                
                            else:
                                sys_cap_ussage()
                                exit(0)    

                            i += 6
                            optionals.append(sys_cap)
                            continue
                        
                        if ((argv[i + 1] == 'sys-cap' or argv[i + 1] == 'SYS-CAP') and \
                            sys_cap != None):
                            print "System capabilities are already set"
                            exit(0)
                            
                        # Can have multiple management address TLVs
                        if(argv[i + 1] == 'mgm-add' or argv[i + 1] == 'MGM-ADD'):
                            if(i + 6 > length - 1):
                                mgm_add_ussage()
                                exit(0)
                            
                            mgm_add = ManagementAddress()
                            add_ok = False
                            
                            if (argv[i + 2] == '-ipv4'):  
                                add_ok = True
                                mgm_add.addrSubtype = 0x01
                                mgm_add.addrStrLen = 1 + 4
                                
                                value = argv[i + 3]
                                val = True
                                try:
                                    IP(value)
                                except:
                                    val = False
                                if(val == False):
                                    mgm_add_ussage()
                                    exit(0)
                                    
                                mgm_add.ipaddr = value
                                
                            if (argv[i + 2] == '-ipv6'):
                                add_ok = True
                                mgm_add.addrSubtype = 0x02
                                mgm_add.addrStrLen = 1 + 16
                                
                                value = argv[i + 3]
                                val = True
                                try:
                                    IPv6(value)
                                except:
                                    val = False
                                if(val == False):
                                    mgm_add_ussage()
                                    exit(0)
                                    
                                mgm_add.ip6addr = value
                                
                            if (argv[i + 2] == '-mgm'):
                                add_ok = True
                                value = argv[i + 3]
                                if(len(value) < 1 or len(value) > 31):
                                    mgm_add_ussage()
                                    exit(0)
                                mgm_add.mgmAddress = value
                                mgm_add.addrStrLen = len(value) + 1
                            
                            if(add_ok == True):
                                    
                                if(argv[i + 4] == '-ifn_subtype'):
                                    if(argv[i + 5] == '-ukn'):
                                        mgm_add.intNumSubtype = 0x01
                                    if(argv[i + 5] == '-index'):
                                        mgm_add.intNumSubtype = 0x02
                                    if(argv[i + 5] == '-port'):
                                        mgm_add.intNumSubtype = 0x03
                                    if(argv[i + 5] != '-ukn' and argv[i + 5] != '-index' and argv[i + 5] != '-port'):
                                        mgm_add_ussage()
                                        exit(0)
                                    mgm_add.ifnumber = int(argv[i + 6])  # considering that it is a correct value
                                    mgm_add.length = mgm_add.addrStrLen + 1 + 4 + 1 + 1  # 1(IntNumsubtype) + 4(ifnumber) + 1(OidLen)+1(oid)
                                    i += 7
                                    optionals.append(mgm_add)
                                    continue
                                    
                                else:
                                    mgm_add_ussage()
                                    exit(0)
                                
                              
                            else:
                                mgm_add_ussage()
                                exit(0)
                        
                        if((argv[i + 1] == 'port-vid' or argv[i + 1] == 'PORT-VID') and \
                           port_vid == None):
                            if(i + 2 > length - 1):
                                port_vid_ussage()
                                exit(0)
                               
                            value = int(argv[i + 2])
                            if(value < 0 or value > 65535):
                                port_vid_ussage()
                                exit(0)
                            port_vid = Port_Vlan_ID()
                            port_vid.length = 6
                            port_vid.PVID = value
                            i += 3
                            optionals.append(port_vid)
                            continue  
                        if((argv[i + 1] == 'port-vid' or argv[i + 1] == 'PORT-VID') and \
                           port_vid != None):
                            print "Port VID is already set"
                            exit(0)
                            
                        # Can have multiple pp-vid TLVs    
                        if(argv[i + 1] == 'pp-vid' or argv[i + 1] == 'PP-VID'):
                            if(i + 4 > length - 1):
                                ppvid_ussage()
                                exit(0)
                            ppvid = Port_And_Protocol_Vlan_ID()
                            ppvid.length = 7
                            ok = False
                            if(argv[i + 2] == '-flags'):
                                if(argv[i + 3] == 'notsup-noten'):
                                    ppvid.flags = 1
                                    ok = True
                                if(argv[i + 3] == 'sup-noten'):
                                    ppvid.flags = 2
                                    ok = True
                                if(argv[i + 3] == 'notsup-en'):
                                    ppvid.flags = 4
                                    ok = True
                                if(argv[i + 3] == 'sup-en'):
                                    ppvid.flags = 6
                                    ok = True
                                if(ok == False):
                                    ppvid_ussage()
                                    exit(0)
                            else:
                                ppvid_ussage()
                                exit(0)  
                              
                            value = int(argv[i + 4])
                            if(value < 0 or value > 65535):
                                ppvid_ussage()
                                exit(0)
                            ppvid.PPVID = value
                            i += 5
                            optionals.append(ppvid)
                            continue  
                     
                        if(argv[i + 1] == 'vlan-name' or argv[i + 1] == 'VLAN-NAME'):
                            if(i + 5 > length - 1):
                                vlan_name_ussage()
                                exit(0)
                            
                            vlan_name = Vlan_Name()
                           
                            if(argv[i + 2] == '-vid'):
                                val1 = int(argv[i + 3])
                                if(val1 < 0 or val1 > 65535):
                                    vlan_name_ussage()
                                    exit(0)
                                vlan_name.VID = val1
                                
                                if(argv[i + 4] == '-vname'):
                                    val2 = argv[i + 5]
                                    if(len(val2) < 0 or len(val2) > 32):
                                        vlan_name_ussage()
                                        exit(0)
                                    vlan_name.nameLength = len(val2)
                                    vlan_name.vlanName = val2
                                    vlan_name.length = 7 + len(val2)
                                    i += 6
                                    optionals.append(vlan_name)
                                    continue  
                                else:
                                    vlan_name_ussage()
                                    exit(0)
                                    
                            else:
                                vlan_name_ussage()
                                exit(0)
                      
                        if (argv[i + 1] == 'prot-id' or argv[i + 1] == 'PROT-ID'):
                            if(i + 2 > length - 1):
                                prot_id_ussage()
                                exit(0)
                            
                            value = argv[i + 2]
                            if(len(value) < 1 or len(value) > 255):
                                prot_id_ussage()
                                exit(0)
                                
                            prot_id = Protocol_Identity()
                            prot_id.length = 5 + len(value)
                            prot_id.identityLength = len(value)
                            prot_id.identity = value
                            i += 3
                            optionals.append(prot_id)
                            continue  
                      
                        if((argv[i + 1] == 'vid-digest' or argv[i + 1] == 'VID-DIGEST') and \
                           vid_digest == None):
                            if(i + 2 > length - 1):
                                vid_ussage_digest()
                                exit(0)
                            
                            value = int(argv[i + 2])
                            vid_dig = VID_Usage_Digest()
                            vid_dig.length = 8
                            vid_dig.VID = value
                            i += 3
                            optionals.append(vid_dig)
                            continue  
                        if((argv[i + 1] == 'vid-digest' or argv[i + 1] == 'VID-DIGEST') and \
                           vid_digest != None):
                            print "Vid Digest is already set"
                            exit(0)
                        
                        if((argv[i + 1] == 'mgm-vid' or argv[i + 1] == 'MGM-VID') and \
                           mgm_vid == None):
                            if(i + 2 > length - 1):
                                mgm_vid_ussage()
                                exit(0)
                            
                            value = int(argv[i + 2])
                            if(value < 0 or value > 65535):
                                mgm_vid_ussage()
                                exit(0)
                            
                            mgm_vid = Management_VID()
                            mgm_vid.length = 6
                            mgm_vid.VID = value
                            i += 3
                            optionals.append(mgm_vid)
                            continue
                        
                        if((argv[i + 1] == 'mgm-vid' or argv[i + 1] == 'MGM-VID') and \
                           mgm_vid != None):
                            print "Management VID is already set"
                            exit(0)
                        
                        if((argv[i + 1] == 'link-agg1' or argv[i + 1] == 'LINK-AGG1') and \
                           link_agg1 == None):
                            if(i + 4 > length - 1):
                                link_agg1_ussage()
                                exit(0)
                            
                            ok = False
                            link_agg1 = Link_Aggregation_Dot1()
                            
                            if(argv[i + 2] == '-status'):
                                if(argv[i + 3] == 'notcap-noten'):
                                    ok = True
                                    link_agg1.status = 0
                                if(argv[i + 3] == 'cap-noten'):
                                    ok = True
                                    link_agg1.status = 1
                                if(argv[i + 3] == 'notcap-en'):
                                    ok = True
                                    link_agg1.status = 2
                                if(argv[i + 3] == 'cap-en'):
                                    ok = True
                                    link_agg1.status = 3
                                    
                                if(ok == False):
                                    link_agg1_ussage()
                                    exit(0)
                            else:
                                link_agg1_ussage()
                                exit(0)
                            
                            value = int(argv[i + 4])
                            link_agg1.PID = value
                            link_agg1.length = 9
                            optionals.append(link_agg1)
                            i += 5
                            continue
                        if((argv[i + 1] == 'link-agg1' or argv[i + 1] == 'LINK-AGG1') and \
                           link_agg1 != None):
                            print "Link aggregation Dot1 is already set"
                            exit(0)
                            
                        if((argv[i + 1] == 'link-agg3' or argv[i + 1] == 'LINK-AGG3') and \
                           link_agg3 == None):
                            if(i + 4 > length - 1):
                                link_agg3_ussage()
                                exit(0)
                            
                            ok = False
                            link_agg3 = Link_Aggregation_Dot3()
                            
                            if(argv[i + 2] == '-status'):
                                if(argv[i + 3] == 'notcap-noten'):
                                    ok = True
                                    link_agg3.status = 0
                                if(argv[i + 3] == 'cap-noten'):
                                    ok = True
                                    link_agg3.status = 1
                                if(argv[i + 3] == 'notcap-en'):
                                    ok = True
                                    link_agg3.status = 2
                                if(argv[i + 3] == 'cap-en'):
                                    ok = True
                                    link_agg3.status = 3
                                    
                                if(ok == False):
                                    link_agg3_ussage()
                                    exit(0)
                            else:
                                link_agg3_ussage()
                                exit(0)
                            
                            value = int(argv[i + 4])
                            link_agg3.PID = value
                            link_agg3.length = 9
                            optionals.append(link_agg3)
                            i += 5
                            continue
                        if((argv[i + 1] == 'link-agg3' or argv[i + 1] == 'LINK-AGG3') and \
                           link_agg3 != None):
                            print "Link aggregation Dot3 is already set"
                            exit(0)
                            
                        if((argv[i + 1] == 'mac-phy' or argv[i + 1] == 'MAC-PHY') and \
                           mac_phy == None):
                            if(i + 7 > length - 1):
                                mac_phy_ussage()
                                exit(0)
                            
                            mac_phy = Mac_Phy_Configuration_Status()
                            ok1 = False
                            
                            if(argv[i + 2] == '-autoneg'):
                                if(argv[i + 3] == 'notsup-noten'):
                                    ok1 = True
                                    mac_phy.autoneg = 0
                                if(argv[i + 3] == 'sup-noten'):
                                    ok1 = True
                                    mac_phy.autoneg = 1
                                if(argv[i + 3] == 'notsup-en'):
                                    ok1 = True
                                    mac_phy.autoneg = 2
                                if(argv[i + 3] == 'sup-en'):
                                    ok1 = True
                                    mac_phy.autoneg = 3
                                    
                                if(ok1 == False):
                                    mac_phy_ussage()
                                    exit(0)
                                    
                                if(argv[i + 4] == '-pmd'):
                                    pmd_value = int(argv[i + 5])
                                    
                                    if(pmd_value < 1 or pmd_value > 16384):
                                        mac_phy_ussage()
                                        exit(0)
                                    mac_phy.PMD = pmd_value
                                    
                                    if(argv[i + 6] == '-mau'):
                                        mau_value = int(argv[i + 7])
                                        if(mau_value < 0 or mau_value > 53):
                                            mac_phy_ussage()
                                            exit(0)
                                        mac_phy.MAU_type = mau_value
                                    
                                    else:
                                        mac_phy_ussage()
                                        exit(0)
                                else:
                                    mac_phy_ussage()
                                    exit(0)
                            else:
                                mac_phy_ussage()
                                exit(0)
                            mac_phy.length = 9
                            optionals.append(mac_phy)
                            i += 8
                            continue
                        if((argv[i + 1] == 'mac-phy' or argv[i + 1] == 'MAC-PHY') and \
                           mac_phy != None):
                            print "MAC/PHY is already set"
                            exit(0)
                            
                        if((argv[i + 1] == 'power' or argv[i + 1] == 'POWER') and \
                           power == None):
                            if(i + 7 > length - 1):
                                power_mdi_ussage()
                                exit(0)
                            
                            power = Power_Via_MDI()
                            
                            if(argv[i + 2] == '-power-support'):
                                value1 = int(argv[i + 3])
                                if(value1 < 0 or value1 > 15):
                                    power_mdi_ussage()
                                    exit(0)
                                power.powerSupport = value1
                                
                                if(argv[i + 4] == '-power-pair'):
                                    value2 = int(argv[i + 5])
                                    if(value2 < 1 or value2 > 2):
                                        power_mdi_ussage()
                                        exit(0)
                                    power.powerPair = value2
                                    
                                    if(argv[i + 6] == '-power-class'):
                                        value3 = int(argv[i + 7])
                                        if(value3 < 1 or value3 > 5):
                                            power_mdi_ussage()
                                            exit(0)
                                        power.powerClass = value3
                                else:
                                    power_mdi_ussage()
                                    exit(0)
                            else:
                                power_mdi_ussage()
                                exit(0) 
                            power.length = 7
                            optionals.append(power)
                            i += 8
                            continue
                        if((argv[i + 1] == 'power' or argv[i + 1] == 'POWER') and \
                           power != None):
                            print "Power Via MDI is already set"
                            exit(0)
                            
                        if((argv[i + 1] == 'max-frame-size' or argv[i + 1] == 'MAX-FRAME-SIZE') and \
                           max_frame == None):
                            if(i + 2 > length - 1):
                                max_frame_ussage()
                                exit(0)
                               
                            value = int(argv[i + 2])
                            if(value < 0 or value > 65535):
                                max_frame_ussage()
                                exit(0)
                                
                            max_frame = Maximum_Frame_Size()
                            max_frame.length = 6
                            max_frame.frameSize = value
                            i += 3
                            optionals.append(max_frame)
                            continue  
                        if((argv[i + 1] == 'max-frame-size' or argv[i + 1] == 'MAX-FRAME-SIZE') and \
                           max_frame != None):    
                            print "Max frame size already set"
                            exit(0)
                            
                        else:  # if none of TLV's name was introduced correctly
                            message2()  # ussage message
                            exit(0)
                        
                    elif((argv[i] != '-tlv' and argv[i] != 'TLV')):
                        message1()
                        exit(0)
                    else:
                        message2()
                        exit(0)
                        
        else:
            print "Other protocols not supported"
            exit(0)
    else:
        message1()
        exit(0)    
        
    return result
