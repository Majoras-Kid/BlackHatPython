import socket

import os
import struct
from ctypes import *

import threading
import time
from netaddr import IPNetwork,IPAddress

#host to listen on
host =      "192.168.2.163"

#subnet to target
subnet =    "192.168.0.0/24"

#magic string we'll check ICMP responses for
magic_message = "PYTHONRULES"

def udp_sender(subnet,magic_message):
    time.sleep(5)
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for ip in IPNetwork(subnet):
    	print "Testing %s" % ip
        try:
            sender.sendto(magic_message,("%s" % ip, 65212))
        except:
            pass    

#our ip header
#for 64bit OS only!
class IP(Structure):

    _fields_ = [
        ("ihl",           c_uint8, 4),
        ("version",       c_uint8, 4),
        ("tos",           c_uint8),
        ("len",           c_uint16),
        ("id",            c_uint16),
        ("offset",        c_uint16),
        ("ttl",           c_uint8),
        ("protocol_num",  c_uint8),
        ("sum",           c_uint16),
        ("src",           c_uint32),
        ("dst",           c_uint32)
    ]

    def __new__(self, socket_buffer=None):
        return self.from_buffer_copy(socket_buffer)    

    def __init__(self, socket_buffer=None):

        # map protocol constants to their names
        self.protocol_map = {1:"ICMP", 6:"TCP", 17:"UDP"}

        # human readable IP addresses
        self.src_address = socket.inet_ntoa(struct.pack("<L",self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L",self.dst))

        # human readable protocol
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            self.protocol = str(self.protocol_num)

class ICMP(Structure):
    
    _fields_ = [
        ("type",            c_uint8),
        ("code",            c_uint8),
        ("checksum",        c_uint16),
        ("unused",          c_uint16),
        ("next_hop_mtu",    c_uint16)
        ]

    def __new__(self, socket_buffer):
        return self.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer):
        pass

        
if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP 
else:
    socket_protocol = socket.IPPROTO_ICMP
    
sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)

sniffer.bind((host, 0))

# we want the IP headers included in the capture
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# if we're on Windows we need to send some ioctls
# to setup promiscuous mode
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

t = threading.Thread(target=udp_sender,args=(subnet,magic_message))
t.start()

try:

    while True:
            #read a package
            raw_buffer = sniffer.recvfrom(65565)[0]
    
        # create an IP header from the first 20 bytes of the buffer
            ip_header = IP(raw_buffer[0:20])
            
            #print out the protocol that was detected and the hosts 
            print "Protocol: %s %s -> %s" % (ip_header.protocol, ip_header.src_address, ip_header.dst_address)

            if ip_header.protocol == "ICMP":

                #calculate where our ICMP packet starts
                offset = ip_header.ihl *4

                buf = raw_buffer[offset:offset+sizeof(ICMP)]

                #create our ICMP structure
                icmp_header = ICMP(buf)

            
                print "ICMP -> Type %d Code: %d" % (icmp_header.type, icmp_header.code)

                #now check for the TYPE 3 and CODE
                if icmp_header.code==3 and icmp_header.type==3 :

                    #make sure host is in out target subnet
                    if IPAddress(ip_header.src_address) in IPNetwork(subnet):

                        #make sure it has our magic message
                        if raw_buffer[len(raw_buffer)-len(magic_message):]==magic_message:
                            
                            print "Host Up: %s" %ip_header.src_address

#handle CTRL-C
except KeyboardInterrupt:

    #if we're using windows, turn off promuscuous mode
    if os.name == "nt":
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)