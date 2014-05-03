from socket import *
import struct
import sys
import time
from datetime import datetime


def GetTimeSNTP(host=None):
    if host is None:
        host = 'ntp.ubuntu.com'
        
    TIME1970 = 2208988800L      # Thanks to F.Lundh

    client = socket( AF_INET, SOCK_DGRAM )
    data = '\x1b' + 47 * '\0'
    client.sendto( data, ( host, 123 ))
    data, address = client.recvfrom( 1024 )
    if data:
        t = struct.unpack( '!12I', data )[10]
        t -= TIME1970
        t = time.localtime(t)
        return datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

