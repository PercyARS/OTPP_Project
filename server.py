#!/usr/bin/env python
# server.py
 
import socket
import select
import Queue
import threading
from threading import *
import urllib2
import sys
 
class Processor(Thread):
    def __init__(self):
        super(Processor, self).__init__()
        self.running = True
        self.q = Queue.Queue()
 
    def add(self, tuple):
        self.q.put(tuple)
 
    def stop(self):
        self.running = False
 
    def run(self):
        q = self.q
        while self.running:
            try:
                # block for 1 second only:
                client, data = q.get(block=True, timeout=1)
                process(client, data)
            except Queue.Empty:
                # waiting for requests
                sys.stdout.write('.')
                sys.stdout.flush()
        #
        if not q.empty():
            print "Elements left in the queue:"
            while not q.empty():
                print q.get()
 

 
def process(client, value):
    """
    Implement this. Do something useful with the received data.
    """
    print value


# fetch tick data every minute
def fetchServer2Data():
    #called every minute
    try:
        data = urllib2.urlopen("https://api.bitcoinaverage.com/history/USD/per_minute_24h_sliding_window.csv")
        for line in data:
            pass
        last = line
        # replace white space by dash
        time = last.split(",")[0]
        time1 = time.split(" ")[0]
        time2 = time.split(" ")[1]
        time = time1+"-"+time2
        # get rid of second
        time1 = time.split(":")[0]
        time2 = time.split(":")[1]
        time = time1+":"+time2
        price = float(last.split(",")[1])
        print ("Adding server2 data time: "+ time+" price: "+str(price))
        Server2Price[time] = price
    except urllib2.URLError, msg:
            print "Server2 read error! %s" % msg
            return -1

#def fetchServer1Data():


def main(port):
    s = socket.socket()
    host = socket.gethostname()
    s.bind((host, port))
    print "Server started, Listening on port {p}...".format(p=port)
    s.listen(5)
    # run forever
    while True:
        try:
            client, addr = s.accept()
            # wait till the client has something for me
            ready = select.select([client], [client], [client], 2)
            if ready[0]:
                data = client.recv(4096)
                # add data and the client socket to the processing queue
                p.add((client, data))
        # catch the ctrl-c
        except KeyboardInterrupt:
            print "Ctrl-c hit, Stop."
            break
        except socket.error, msg:
            print "Socket error! %s" % msg
            break
    #stop the thread and return 0
    cleanup()
    return 0
 
def cleanup():
    t.cancel()
    t.join()
    p.stop()
    p.join()
 
#########################################################
p = Processor()
p.start()
# fecth from server2 for every 1 minute
t = threading.Timer(60.00, fetchServer2Data)
t.start()
# initialize the Server2Price dictionary
Server2Price = {}

if __name__ == "__main__":
    if len(sys.argv) not in [1,2]:
        print ("Server exits: invalid number of arguments")
    elif len(sys.argv) == 2 and sys.argv[1].isdigit() == False:
        print ("Server exists: invalid type of arguments")
    elif len(sys.argv) == 2 and int(sys.argv[1]) not in range(65537):
        print ("Server exits: invalid port number")
    else:
        # if port not given, use the default 8000
        port = 8000 if len(sys.argv) == 1 else int(sys.argv[1])
        if fetchServer2Data() == -1:
            exit(-1)
        exit(main(port))