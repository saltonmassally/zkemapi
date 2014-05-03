
import logging
import socket
from struct import pack, unpack
from datetime import datetime, date


logger = logging.getLogger('zkem.logger')

USHRT_MAX = 65535


# These commands came from cmds.h
CMD_CONNECT = 1000
CMD_EXIT = 1001
CMD_ENABLEDEVICE = 1002
CMD_DISABLEDEVICE = 1003

CMD_ACK_OK = 2000
CMD_ACK_ERROR = 2001
CMD_ACK_DATA = 2002

CMD_PREPARE_DATA = 1500
CMD_DATA = 1501

CMD_USERTEMP_RRQ = 9
CMD_ATTLOG_RRQ = 13
CMD_CLEAR_DATA = 14
CMD_CLEAR_ATTLOG = 15

CMD_WRITE_LCD = 66

CMD_GET_TIME  = 201
CMD_SET_TIME  = 202



def encode_time(t):
    """Encode a timestamp send at the timeclock

    copied from zkemsdk.c - EncodeTime"""
    d = ( (t.year % 100) * 12 * 31 + ((t.month - 1) * 31) + t.day - 1) *\
         (24 * 60 * 60) + (t.hour * 60 + t.minute) * 60 + t.second

    return d


def decode_time(t):
    """Decode a timestamp retrieved from the timeclock

    copied from zkemsdk.c - DecodeTime"""
    second = t % 60
    t = t / 60

    minute = t % 60
    t = t / 60

    hour = t % 24
    t = t / 24

    day = t % 31+1
    t = t / 31

    month = t % 12+1
    t = t / 12

    year = t + 2000

    d = datetime(year, month, day, hour, minute, second)

    return d

class zkem(object):

    def __init__(self):
        
        self.host  = None
        self.port  = 0
        self.debug = False
        self.__userdata = []
        self.__userdata
        self.__logdata = []
        self.__s   = None
        self.__session_id = 0
        
    def __in_chksum(self,p):
        """This function calculates the chksum of the packet to be sent to the 
        time clock

        Copied from zkemsdk.c"""
        l = len(p)
        chksum = 0
        while l > 1:
            chksum += unpack('H', pack('BB', p[0], p[1]))[0]
            p = p[2:]
            if chksum > USHRT_MAX:
                chksum -= USHRT_MAX
            l -= 2
        if l:
            if self.debug:
                logger.debug( l )
            chksum = chksum + p[-1]
        while chksum > USHRT_MAX:
            chksum -= USHRT_MAX
        chksum = ~chksum
        while chksum < 0:
            chksum += USHRT_MAX
        return pack('H', chksum)

    def __construct_header(self, command, chksum, session_id, reply_id, 
                                command_string):
        """This function puts a the parts that make up a packet together and 
        packs them into a byte string"""
        buf = pack('HHHH', command, chksum,
            session_id, reply_id) + command_string

        if self.debug > 1:
            logger.debug("Command String Length: " + str(len(command_string)))
        buf = unpack('8B'+'%sB' % len(command_string), buf)

        chksum = unpack('H', self.__in_chksum(buf))[0]
        reply_id += 1
        if reply_id >= USHRT_MAX:
            reply_id -= USHRT_MAX

        buf = pack('HHHH', command, chksum, session_id, reply_id)
        return buf + command_string
    

    def __connect_command(self):
        """Start a connection with the time clock"""
        command = CMD_CONNECT
        command_string = ''
        chksum = 0
        session_id = 0
        reply_id = -1 + USHRT_MAX

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Connecting")

        return buf

    def __disconnect_command(self,reply):
        """Disconnect from the clock"""
        command = CMD_EXIT
        command_string = ''
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Disconnecting")

        return buf


    def __disable_device_command(self,reply):
        
        """Disable the timeclock. Show "Working..." on the clock and makes it
        unusable"""
        command = CMD_DISABLEDEVICE
        command_string = '\x00\x00'
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Disabling Device")

        return buf
    
    def __enable_device_command(self,reply):
        """Enable the timeclock. Makes the clock work again, after disabling it"""
        command = CMD_ENABLEDEVICE
        command_string = ''
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]
      
        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Enabling Device")

        return buf
        
    
    def __get_user_data_command(self,reply):
        """Gets the timeclock to send the user data"""
        command = CMD_USERTEMP_RRQ
        command_string = '\x05'
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Getting User Data")

        return buf


    def __get_attendance_log_command(self,reply):
        """gets the timeclock to send the attendance log"""
        command = CMD_ATTLOG_RRQ
        command_string = ''
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Getting Attendance Log")

        return buf
        
        
    def __clear_attendance_log_command(self,reply):
        """clears the attendance log the timeclock to send"""
        command = CMD_CLEAR_ATTLOG
        command_string = ''
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Cleaning Attendance Log")

        return buf

    def __set_time_command(self,reply,t):
        """Set Time from the clock"""
        command = CMD_SET_TIME
        command_string = pack('I',encode_time(t))
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Set Time")

        return buf


    def __get_time_command(self,reply):
        """Get Time from the clock"""
        command = CMD_GET_TIME
        command_string = ''
        chksum = 0
        session_id = self.__session_id #unpack('HHHH', reply[:8])[2]
        reply_id = unpack('HHHH', reply[:8])[3]

        buf = self.__construct_header(command, chksum, session_id,
            reply_id, command_string)
        if self.debug:
            logger.debug("Get Time")

        return buf

            
    def __check_ack_ok(self,reply):
        """Checks a returned packet to see if it returned CMD_ACK_OK,
        indicating success"""
        command = unpack('HHHH', reply[:8])[0]
        if command == CMD_ACK_OK:
            if self.debug:
                logger.debug("Success")
            return True
        else:
            if self.debug:
                logger.debug("Failure")
            return False
            
    def __check_ack_data(self,reply):
        """Checks a returned packet to see if it returned CMD_ACK_DATA,
        indicating a data packet"""
        command = unpack('HHHH', reply[:8])[0]
        if command == CMD_ACK_DATA:
            if self.debug:
                logger.debug("Data is going to be sent")
            return True
        else:
            if self.debug:
                logger.debug("Failure, data is not going to be sent")
            return False

    def __check_prepare_data(self,reply):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent
    
        Returns the amount of bytes that are going to be sent"""
        command = unpack('HHHH', reply[:8])[0] 
        if command == CMD_PREPARE_DATA:
            if self.debug:
                logger.debug("Data is going to be sent")
            size = unpack('I', reply[8:12])[0]
            if self.debug:
                logger.debug("%d bytes will be sent" % size)
            return size
        else:
            if self.debug:
                logger.debug("Failure, data is not going to be sent")
            return False
        
        
    def connect(self, host = None, port = 4370, timeout = 60, debug = False):
        
        # Valid parameters 
        self.debug = debug
        if host is None:
            if self.debug:
                logger.debug("host not define")
            return False
            
        self.host  = host
        self.port  = port
        
        
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__s.settimeout(timeout)
        self.__s.connect((self.host, self.port))

        # Connect to the timeclock
        self.__s.send(self.__connect_command())
        try:
            self.__reply = self.__s.recv(8)
            self.__session_id = unpack('HHHH', self.__reply[:8])[2]
            return self.__check_ack_ok(self.__reply)
        except:
            return False
        
        
    def disconnect(self):
         # Disconnect from the timeclock
        self.__s.send(self.__disconnect_command(self.__reply))
        self.__reply = self.__s.recv(8)
        self.__s.close()
        return self.__check_ack_ok(self.__reply)
        
        
    def disable(self):
        # Disable the timeclock
        self.__s.send(self.__disable_device_command(self.__reply))
        self.__reply = self.__s.recv(8)
        return self.__check_ack_ok(self.__reply)
        
        
    def enable(self):
        # Enable the timeclock, as it was disabled earlier
        self.__s.send(self.__enable_device_command(self.__reply))
        self.__reply = self.__s.recv(8)
        return self.__check_ack_ok(self.__reply)
        
    
    def get_user_data(self):
        # Get User data from the timeclock
        self.__s.send(self.__get_user_data_command(self.__reply))
        self.__reply = self.__s.recv(16)

        self.__userdata = []
        if self.__check_prepare_data(self.__reply):
            bytes = self.__check_prepare_data(self.__reply)
            while bytes > 0:
                # Receive 1024 bytes of data plus 8 byte header
                #self.__userdata.append(self.__s.recv(1032)[8:])
                self.__userdata.append(self.__s.recv(1032))
                bytes -= 1024

        # after the data is sent, another packet is sent, indicating success
        sr = self.__s.recv(8)
        return self.__check_ack_ok(sr)
   

    def unpack_user_data(self):

        # Create a dictionary of user id s to user names 
        users = {}
        if len(self.__userdata) > 0:
            # The first 4 bytes don't seem to be related to the user
            self.__userdata = self.__userdata[4:]

            while (len(self.__userdata) / 28) > 0:
                uid, name = unpack('h6x8s12x', self.__userdata[:28])
        
                # Clean up some messy characters from the user name
                name = unicode(name.strip('\x00|\x01\x10x'), errors='ignore')
                if name.strip() == "":
                    name = uid
                users[uid] = name
                #if self.debug:
                print("%s, %s" % (uid, name))
                self.__userdata = self.__userdata[28:]

        return users
 
    def get_attendance_log(self):
        # Get the attendance log data
        self.__s.send(self.__get_attendance_log_command(self.__reply))
        self.__reply = self.__s.recv(16)

        self.__logdata = []
        if self.__check_prepare_data(self.__reply):
            bytes = self.__check_prepare_data(self.__reply)
            while bytes > 0:
                # Receive 1024 bytes of data plus 8 byte header
                self.__logdata.append(self.__s.recv(1032)[8:])
                #self.__logdata.append(self.__s.recv(1032))
                bytes -= 1024
    
        if len(self.__logdata) > 0:
            # after the data is sent, another packet is sent, indicating success
            sr = self.__s.recv(8)
            return self.__check_ack_ok(sr)
        return False
        
    def unpack_attendance_log(self):
        
        log = []
        if len(self.__logdata) > 0:
            
            # Copy the attendance log data to one big byte string
            l = []
            for i in self.__logdata:
                l.append(i)

            ls = "".join(l)
            # The first 4 bytes don't seem to be the right sort of data
            ls = ls[4:]

            # Split the attendance log data into a list of each entry
            l = []
            while((len(ls) / 8.0) >= 1):  # 16.
                l.append(ls[:8])          # :16  
                ls = ls[8:]               # 16

            # Decode all the log entries 
            state_dict = {0: "Check In (Code)",
                          8: "Check In (Fingerprint)",
                         32: "Check Out (Code)",
                         40: "Check Out (Fingerprint)"}
            
            for i in l:
                uid, state, timestamp = unpack('HHI', i[:8])
                timestamp = decode_time(timestamp)

                if timestamp != datetime(2000, 1, 1, 0, 0):
                    if state_dict.has_key(state):
                        state = state_dict[state]
                        log.append([uid, timestamp, state])
        return log


    def clear_attendance_log(self):
        # Get the attendance log data
        if len(self.__logdata) > 0:
            self.__s.send(self.__clear_attendance_log_command(self.__reply))
            self.__reply = self.__s.recv(16)
            return self.__check_ack_ok(self.__reply)


    def set_time(self,t):
        # Get time
        self.__s.send(self.__set_time_command(self.__reply,t))
        self.__reply = self.__s.recv(8)
        return self.__check_ack_ok(self.__reply)


    def get_time(self):
        # Get time
        self.__s.send(self.__get_time_command(self.__reply))
        self.__reply = self.__s.recv(12)
        if self.__check_ack_ok(self.__reply):
            timestamp = unpack('HHHI', self.__reply)[3]
            return decode_time(timestamp)

        return None

