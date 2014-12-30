'''
Created on Jun 10, 2013

@author: Alexandru Nicolae
'''

def message1():
    msg = "tool -p lldp -tlv 'type' [-subtype] 'value'\n"
    msg = msg + " "*12
    msg = msg + "[-i sending interface]\n";   
    print msg

def message2():
    msg = "tool -p lldp -tlv [ chid \t\t ChassisID ]\n"
    msg = msg + " "*18
    msg = msg + "[ port-id \t\t PortID ]\n"
    msg = msg + " "*18
    msg = msg + "[ TTL \t\t Time to Live ]\n"
    msg = msg + " "*18
    msg = msg + "[ port-desc \t\t Port Description ]\n"
    msg = msg + " "*18
    msg = msg + "[ sys-name \t\t System Name ]\n"
    msg = msg + " "*18
    msg = msg + "[ sys-desc \t\t System Description ]\n"
    msg = msg + " "*18
    msg = msg + "[ sys-cap \t\t System Capabilites ]\n"
    msg = msg + " "*18
    msg = msg + "[ mgm-add \t\t Management Address ]\n"
    msg = msg + " "*18
    msg = msg + "[ port-vid \t\t Port Vlan ID ]\n"
    msg = msg + " "*18
    msg = msg + "[ pp-vid \t\t Port and Protocol Vlan ID ]\n"
    msg = msg + " "*18
    msg = msg + "[ vlan-name \t\t Vlan Name ]\n"
    msg = msg + " "*18
    msg = msg + "[ prot-id \t\t Protocol Identity ]\n"
    msg = msg + " "*18
    msg = msg + "[ vid-digest \t\t VID Usage Digest ]\n"
    msg = msg + " "*18
    msg = msg + "[ mgm-vid \t\t Management VID ]\n"
    msg = msg + " "*18
    msg = msg + "[ link-agg1 \t\t Link Aggregation as 802.1 Subtype ]\n"
    msg = msg + " "*18
    msg = msg + "[ link-agg3 \t\t Link Aggregation as 802.3 Subtype ]\n"
    msg = msg + " "*18
    msg = msg + "[ mac-phy \t\t MAC/PHY Configuration Status ]\n"
    msg = msg + " "*18
    msg = msg + "[ power \t\t Power Via MDI ]\n"
    msg = msg + " "*18
    msg = msg + "[ max-frame-size \t Maximum frame size ]\n"
    print msg
    
def chid_ussage():
    msg = "tool -p lldp -tlv chid [ -chassis-comp \t Chassis Component ] \t 'value': [1,255] octets\n"
    msg = msg + " "*23
    msg = msg + "[ -int-alias \t Interface alias ] \t 'value': [1,255] octets\n"
    msg = msg + " "*23
    msg = msg + "[ -port-comp \t Port component ] \t 'value': [1,255] octets\n"
    msg = msg + " "*23
    msg = msg + "[ -mac-addr \t Mac address ] \t\t 'value': xx:xx:xx:xx:xx:xx\n"
    msg = msg + " "*23
    msg = msg + "[ -ipv4 \t\t IP version 4 ] \t 'value': A.B.C.D\n"
    msg = msg + " "*23
    msg = msg + "[ -ipv6 \t\t IP version 6 ] \t 'value': A.B.C.D.E.F.G.H.I\n"
    msg = msg + " "*23
    msg = msg + "[ -int-name \t Interface name ] \t 'value': [1,255] octets\n"
    msg = msg + " "*23
    msg = msg + "[ -local \t Locally assigned ] \t 'value': [1,255] octets\n"
    print msg

def portid_ussage():
    msg = "tool -p lldp -tlv portid [ -int-alias \t Interface Alias ] \t 'value': [1,255] octets\n"
    msg = msg + " "*25
    msg = msg + "[ -port-comp \t Port component ] \t 'value': [1,255] octets\n"
    msg = msg + " "*25
    msg = msg + "[ -mac-addr \t Mac address ] \t\t 'value': xx:xx:xx:xx:xx:xx\n"
    msg = msg + " "*25
    msg = msg + "[ -ipv4 \t IP version 4 ] \t 'value': A.B.C.D\n"
    msg = msg + " "*25
    msg = msg + "[ -ipv6 \t IP version 6 ] \t 'value': A.B.C.D.E.F.G.H\n"
    msg = msg + " "*25
    msg = msg + "[ -int-name \t Interface name ] \t 'value': [1,255] octets\n"
    msg = msg + " "*25
    msg = msg + "[ -agent-id \t Agent Circuit ID ] \t 'value': [1,255] octets\n"
    msg = msg + " "*25
    msg = msg + "[ -local \t Locally assigned ] \t 'value': [1,255] octets\n"
    print msg

def ttl_ussage():
    msg = "tool -p lldp -tlv ttl value: [0,65535]\n"
    print msg
    
def port_desc_ussage():
    msg = "tool -p lldp -tlv port-desc value: [0,255] octets\n"
    print msg

def sys_name_ussage():
    msg = "tool -p lldp -tlv sys-name value: [0,255] octets\n"
    print msg
    
def sys_desc_ussage():
    msg = "tool -p lldp -tlv sys-desc value: [0,255] octets\n"
    print msg
    
def sys_cap_ussage():
    msg = "tool -p lldp -tlv sys-cap -system [ other \t Other ]"
    msg = msg + "\t-enabled [other|repeater|...|tprelay]\n"
    msg = msg + " "*33
    msg = msg + " [ repeater \t Repeater ]\n"
    msg = msg + " "*33
    msg = msg + " [ bridge \t Bridge ]\n"
    msg = msg + " "*33
    msg = msg + " [ ap \t\t Access Point ]\n"
    msg = msg + " "*33
    msg = msg + " [ router \t Router ]\n"
    msg = msg + " "*33
    msg = msg + " [ phone \t Telephone ]\n"
    msg = msg + " "*33
    msg = msg + " [ docsis \t Docsis cable device ]\n"
    msg = msg + " "*33
    msg = msg + " [ station \t Station only ]\n"
    msg = msg + " "*33
    msg = msg +" [ cvlan \t C-Vlan ]\n"
    msg = msg + " "*33
    msg = msg + " [ svlan \t S-Vlan ]\n"
    msg = msg + " "*33
    msg = msg + " [ tprelay \t Two Port Mac Relay ]\n"
    msg = msg + " "*33
    msg = msg + " [ SEPARATED BY COMMAS ]\n"
    print msg

def mgm_add_ussage():
    msg = "tool -p lldp -tlv mgm-add [ -ipv4 \t IP version 4 ] \t 'value'\n"
    msg = msg + " "*26
    msg = msg + "[ -ipv6 \t IP version 6 ] \t 'value'\n"
    msg = msg + " "*26
    msg = msg + "[ -mgm \t Another management address: [1,31] octets ] \t 'value'\n"
    msg = msg + " "*26
    msg = msg + "-ifn_subtype "
    msg = msg + "[-ukn \t Unkown] \t   'value': Interface Number\n"
    msg = msg + " "*39
    msg = msg + "[-index \t Interface Index]\n"
    msg = msg + " "*39
    msg = msg + "[-port \t Port Number]\n"
    print msg
    
def port_vid_ussage():
    msg = "tool -p lldp -tlv port-vid value: [0,65535]\n"
    print msg

def ppvid_ussage():
    msg = "tool -p lldp -tlv pp-vid -flags "
    msg = msg + "[ notsup-noten \t Not supported and Not enabled]\n"
    msg = msg + " "*32
    msg = msg + "[ sup-noten \t Supported and Not enabled]\n"
    msg = msg + " "*32
    msg = msg + "[ notsup-en \t Supported and Not enabled]\n"
    msg = msg + " "*32
    msg = msg + "[ sup-en \t Supported and Enabled]\n"
    msg = msg + " "*32
    msg = msg + "'value': \t [0,65535]\n"
    print msg

def vlan_name_ussage():
    msg = "tool -p lldp -tlv vlan-name -vid 'value': [0,65535]\n"
    msg = msg + " "*28
    msg = msg + "-vname 'value': [0,32] octets"
    print msg

def prot_id_ussage():
    msg = "tool -p lldp -tlv prot-id 'value': [1,255] octets\n"
    print msg

def vid_ussage_digest():
    msg = "tool -p lldp -tlv vid-digest 'value': 4 octets\n"
    print msg

def mgm_vid_ussage():
    msg = "tool -p lldp -tlv mgm-vid 'value': [0,65535]\n"
    print msg
    
def link_agg1_ussage():
    msg = "tool -p lldp -tlv link-agg1 -status "
    msg = msg + "[ notcap-noten \t Not capable of aggregation and Not enabled]\n"
    msg = msg + " "*36
    msg = msg + "[ cap-noten \t Capable of aggregation and Not enabled]\n"
    msg = msg + " "*36
    msg = msg + "[ notcap-en \t Not capable of aggregation and enabled]\n"
    msg = msg + " "*36
    msg = msg + "[ cap-en \t\t Capable and Enabled]\n"
    msg = msg + " "*36
    msg = msg + "'pid-value': \t PortID value: 4 octets\n"
    print msg
    
def link_agg3_ussage():
    msg = "tool -p lldp -tlv link-agg3 -status "
    msg = msg + "[ notcap-noten \t Not capable of aggregation and Not enabled]\n"
    msg = msg + " "*36
    msg = msg + "[ cap-noten \t Capable of aggregation and Not enabled]\n"
    msg = msg + " "*36
    msg = msg + "[ notcap-en \t Not capable of aggregation and enabled]\n"
    msg = msg + " "*36
    msg = msg + "[ cap-en \t\t Capable and Enabled]\n"
    msg = msg + " "*36
    msg = msg + "'pid-value': \t PortID value: 4 octets\n"
    
    print msg

def mac_phy_ussage():
    msg = "tool -p lldp -tlv mac-phy -autoneg "
    msg = msg + "[ notsup-noten \t Not Supported and Not enabled ]\n"
    msg = msg + " "*35
    msg = msg + "[ sup-noten \t\t Supported and Not enabled ]\n"
    msg = msg + " "*35
    msg = msg + "[ notsup-en \t\t Not Supported and Enabled ]\n"
    msg = msg + " "*35
    msg = msg + "[ sup-en \t\t Supported and Enabled ]\n\n"
    msg = msg + " "*26
    msg = msg + "-pmd" + " "*5 + "[ 1 \t\t 1000BASE-T full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 2 \t\t 1000BASE-T half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 4 \t\t 1000BASE-X, -LX, -SX, -CX full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 8 \t\t 1000BASE-X, -LX, -SX, -CX half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 16 \t Asymmetric and Symmetric PAUSE for full-duplex inks ]\n"
    msg = msg + " "*35
    msg = msg + "[ 32 \t Symmetric PAUSE for full-duplex links ]\n"
    msg = msg + " "*35
    msg = msg + "[ 64 \t Asymmetric PAUSE for full-duplex links ]\n"
    msg = msg + " "*35
    msg = msg + "[ 128 \t PAUSE for full-duplex links ]\n"
    msg = msg + " "*35
    msg = msg + "[ 256 \t 100BASE-T2 full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 512 \t 100BASE-T2 half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 1024 \t 100BASE-TX full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 2048 \t 100BASE-TX half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 4096 \t 100BASE-T4 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 8192 \t 100BASE-T full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 16384 \t 10BASE-T half duplex mode ]\n\n"
    msg = msg + " "*26
    msg = msg + "-mau" + " "*5 + "[ 0 \t\t other or unknown ]\n"
    msg = msg + " "*35
    msg = msg + "[ 1 \t\t AUI ]\n"
    msg = msg + " "*35
    msg = msg + "[ 2 \t\t 10BASE-5 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 3 \t\t FOIRL ]\n"
    msg = msg + " "*35
    msg = msg + "[ 4 \t\t 10BASE-2 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 5 \t\t 10BASE-T duplex mode unknown ]\n"
    msg = msg + " "*35
    msg = msg + "[ 6 \t\t 10BASE-FP ]\n"
    msg = msg + " "*35
    msg = msg + "[ 7 \t\t 10BASE-FB ]\n"
    msg = msg + " "*35
    msg = msg + "[ 8 \t\t 10BASE-FL duplex mode unknown ]\n"
    msg = msg + " "*35
    msg = msg + "[ 9 \t\t 10BROAD36 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 10 \t 10BASE-T  half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 11 \t 10BASE-T  full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 12 \t 10BASE-FL half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 13 \t 10BASE-FL full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 14 \t 100BASE-T4 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 15 \t 100BASE-TX half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 16 \t 100BASE-TX full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 17 \t 100BASE-FX half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 18 \t 100BASE-FX full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 19 \t 100BASE-T2 half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 20 \t 100BASE-T2 full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 21 \t 1000BASE-X half duplex mode  ]\n"
    msg = msg + " "*35
    msg = msg + "[ 22 \t 1000BASE-X full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 23 \t 1000BASE-LX half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 24 \t 1000BASE-LX full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 25 \t 1000BASE-SX half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 26 \t 1000BASE-SX full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 27 \t 1000BASE-CX half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 28 \t 1000BASE-CX full duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 29 \t 1000BASE-T half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 30 \t 1000BASE-T half duplex mode ]\n"
    msg = msg + " "*35
    msg = msg + "[ 31 \t 10GBASE-X ]\n"
    msg = msg + " "*35
    msg = msg + "[ 32 \t 10GBASE-LX4 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 33 \t 10GBASE-R ]\n"
    msg = msg + " "*35
    msg = msg + "[ 34 \t 10GBASE-ER ]\n"
    msg = msg + " "*35
    msg = msg + "[ 35 \t 10GBASE-LR ]\n"
    msg = msg + " "*35
    msg = msg + "[ 36 \t 10GBASE-SR ]\n"
    msg = msg + " "*35
    msg = msg + "[ 37 \t 10GBASE-W ]\n"
    msg = msg + " "*35
    msg = msg + "[ 38 \t 10GBASE-EW ]\n"
    msg = msg + " "*35
    msg = msg + "[ 39 \t 10GBASE-LW ]\n"
    msg = msg + " "*35
    msg = msg + "[ 40 \t 10GBASE-SW ]\n"
    msg = msg + " "*35
    msg = msg + "[ 41 \t 10GBASE-CX4 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 42 \t 2BASE-TL ]\n"
    msg = msg + " "*35
    msg = msg + "[ 43 \t 10PASS-TS ]\n"
    msg = msg + " "*35
    msg = msg + "[ 44 \t 100BASE-BX10D ]\n"
    msg = msg + " "*35
    msg = msg + "[ 45 \t 100BASE-BX10U ]\n"
    msg = msg + " "*35
    msg = msg + "[ 46 \t 100BASE-LX10 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 47 \t 1000BASE-BX10D ]\n"
    msg = msg + " "*35
    msg = msg + "[ 48 \t 1000BASE-BX10U ]\n"
    msg = msg + " "*35
    msg = msg + "[ 49 \t 1000BASE-LX10 ]\n"
    msg = msg + " "*35
    msg = msg + "[ 50 \t 1000BASE-PX10D ]\n"
    msg = msg + " "*35
    msg = msg + "[ 51 \t 1000BASE-PX10U ]\n"
    msg = msg + " "*35
    msg = msg + "[ 52 \t 1000BASE-PX20D ]\n"
    msg = msg + " "*35
    msg = msg + "[ 53 \t 1000BASE-PX20U ]\n"
    print msg

def power_mdi_ussage():
    msg = "tool -p lldp -tlv power -power-support "
    msg = msg + "[0 \t Port class PD  ]\n"
    msg = msg + " "*39
    msg = msg + "[1 \t Port class PSE ]\n"
    msg = msg + " "*39
    msg = msg + "[2 \t MDI power support: supported ]\n"
    msg = msg + " "*39
    msg = msg + "[3 \t MDI power support: supported - Port class PSE ]\n"
    msg = msg + " "*39
    msg = msg + "[4 \t MDI power state: enabled ]\n"
    msg = msg + " "*39
    msg = msg + "[5 \t MDI power state: enabled - Port class PSE ]\n"
    msg = msg + " "*39
    msg = msg + "[6 \t MDI power state: enabled - MDI power support: supported ]\n"
    msg = msg + " "*39
    msg = msg + "[7 \t MDI power state: enabled - MDI power support: supported - Port class PSE ]\n"
    msg = msg + " "*39
    msg = msg + "[8 \t Pair control: enabled ]\n"
    msg = msg + " "*39
    msg = msg + "[9 \t Pair control: enabled - Port class PSE ]\n"
    msg = msg + " "*39
    msg = msg + "[10 \t Pair control: enabled - MDI power support: supported ]\n"
    msg = msg + " "*39
    msg = msg + "[11 \t Pair control: enabled - MDI power support: supported - PSE ]\n"
    msg = msg + " "*39
    msg = msg + "[12 \t Pair control: enabled - MDI power state: enabled ]\n"
    msg = msg + " "*39
    msg = msg + "[13 \t Pair control: enabled - MDI power state: enabled - PSE ]\n"
    msg = msg + " "*39
    msg = msg + "[14 \t Pair control: enabled - MDI power state: enabled - MDI power support: supported ]\n"
    msg = msg + " "*39
    msg = msg + "[15 \t Pair control: enabled - MDI power state: enabled - MDI power support: supported - PSE ]\n\n"
    msg = msg + " "*24
    msg = msg + "-power-pair" + " "*4 + "[1 \t Signal pairs only are in use ]\n"
    msg = msg + " "*39
    msg = msg + "[2 \t The spare pairs only are in use ]\n\n"
    msg = msg + " "*24
    msg = msg + "-power-class" + " "*3 + "[1 \t Class 1 ]\n"
    msg = msg + " "*39
    msg = msg + "[2 \t Class 2 ]\n"
    msg = msg + " "*39
    msg = msg + "[3 \t Class 3 ]\n"
    msg = msg + " "*39
    msg = msg + "[4 \t Class 4 ]\n"
    msg = msg + " "*39
    msg = msg + "[5 \t Class 5 ]\n"
    print msg

def max_frame_ussage():
    msg = "tool -p lldp -tlv max-frame-size value: [0,65535]\n"
    print msg    
    
