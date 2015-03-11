import socket
import sys
import logging
import threading
from os.path import expanduser

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 5000 # Arbitrary non-privileged port
DELAY = 1

home = expanduser("~")

logger = logging.getLogger('apm-dome')
hdlr = logging.FileHandler(home + '/apm-log/apm-dome.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

class Open (threading.Thread):

        # position = 0;

        def __init__(self):
                threading.Thread.__init__(self)
                # self.stopped = event
                self.position = 0

        def run(self):
                for i in range(0, 101, 10):
                        self.position = i
                        time.sleep(1)
		logger.info ("Dome opened")
		

class Close (threading.Thread):

        # position = 0;

        def __init__(self):
                threading.Thread.__init__(self)
                # self.stopped = event
                self.position = 100

        def run(self):
                for i in range(100, -1, -10):
                        self.position = i
                        time.sleep(1)
		logger.info ("Dome closed")

# status
#	1 - opening
#	2 - closing
#	3 - opened
#	4 - closed
# position

def domestop():
	global status
	global dome

	# dome.stop()

	status = 5;

def domeopen ():
	global status
	global dome

	if status == 1 or status == 2:	# moving                
		return

	if status == 4: # dome closed
		status = 1
		dome = Open()
		dome.start()
		return

	if status == 3: # opened already
		logger.info ("Already opened")
		return

def domeclose ():
	global status
	global dome

	if status == 1 or status == 2:	# moving
		return;

	if status == 4:	# closed already
		logger.info("Already closed")
		return

	if status == 3:	#opened
		status = 2
		dome = Close()
		dome.start()
		return

def set(a):
        global status

        if a == '000':
                logger.info("Dome: trying to close")
		domeclose ()
	elif a == '100':
		logger.info("Dome: trying to open")
                domeopen ()
	elif a == '777':
		logger.info("Dome: close (init)")
		domeclose ()
	elif a == '666':
		logger.info("Dome: emergency stop");
		domestop ()
	elif a == '999':
		logger.info("RTS2 asked for info")

def ret():
        global status
	global dome

	if dome.position == 100:
		status = 3
	if dome.position == 0:
		status = 4

        if   status == 1:	# opening
		toret = 'D91%03d1%03d' % (dome.position, dome.position)	
        elif status == 2:	# closing
                toret = 'D92%03d2%03d' % (dome.position, dome.position)
        elif status == 3:	# opened
                toret = 'D901000100'	 
	elif status == 4:	# closed
		toret = 'D900000000'
	elif status == 5:
		toret = 'D93%03d3%03d' % (dome.position, dome.position)

	logger.info("Message to the client: " + toret);
	return toret

# Datagram (udp) socket
try :
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	logger.info("Socket created")
except socket.error, msg :
	logger.error("Failed to create socket. Error Code : " + str(msg[0]) + " Message " + msg[1])
	sys.exit()
 
# Bind socket to local host and port
try:
	s.bind((HOST, PORT))
except socket.error , msg:
	logger.error('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
	sys.exit()
     
logger.info('Socket bind complete')
 
status = 4
dome = Open();

# now keep talking with the client
while 1:
	# receive data from client (data, addr)
	d = s.recvfrom(1024)
	data = d[0]
	addr = d[1]
	
	if not data: 
        	break
     
	logger.info('Command from [' + addr[0] + ':' + str(addr[1]) + '] - ' + data.strip())

	i = data[1:]
	s.sendto(ret(), addr) 
	set(i)

s.close()
