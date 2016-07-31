#!/usr/bin/env python
# server.py
 
import socket
import select
import Queue
import threading
from threading import *
import urllib2
import sys
import gzip
import datetime
import numpy as np

# class object that encapsulates data per minute



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
    Price[time] = price

def linuxToUTC(linuxTime):
    return datetime.datetime.fromtimestamp(int(linuxTime)).strftime('%Y-%m-%d-%H:%M')

def fetchServer1Data():
    print 'Prcocessing Server1 Data'
    dataFile = urllib2.URLopener()
    dataFile.retrieve('http://api.bitcoincharts.com/v1/csv/bitfinexUSD.csv.gz', "past.csv.gz")
    with gzip.open('past.csv.gz','rt') as f:
        for line in f:
            time1 = int(line.split(",")[0])
            # find the closest minute
            time = time1 - time1 % 60
            price = line.split(",")[1]
            Price[time] = price
    # initialize the data structure
    firstDataTime = Price.keys()[0]
    lastPrice = Price[firstDataTime]
    lastTime = firstDataTime
    Signal[firstDataTime] = 0
    S_avg = {firstDataTime:Price[firstDataTime]}
    Sigma = {firstDataTime:0}
    PnL = {firstDataTime:0}
    csv_file = open("Server1Result.csv", "w")
    csv_file.write("datetime, price, signal, pnl\n")

    for time in Price.keys()[1:]:
        HourList = []
        #if its less than 24 hour since start time, we use whatever we have
        if time <= firstDataTime + 86400:
            HourList = [Price[i] for i in Price.keys() if i <= time]
        # there are enough elements to calculate the window
        else:
            startTime = time - 86400
            HourList = [Price[i] for i in Price.keys() if i <= time and i >= startTime]
        S_avg[time] = np.mean(HourList)
        Sigma[time] = np.std(HourList)
        # calculate signal
        lastSignal = Signal[Signal.keys()[-1]]
        if lastPrice > S_avg[lastTime] + Sigma[lastTime]:
            Signal[time] = 1
        elif lastPrice < S_avg[lastTime] - Sigma[lastTime]:
            Signal[time] = -1
        else:
            Signal[time] = lastSignal
        # calculate P&L
        if time == firstDataTime:
            pass
        else:
            PnL[time] = lastSignal * (Price[time]/lastPrice-1)
        # keep the last price
        lastTime = time
        lastPrice = Price[time]
        print ("Writing:"+linuxToUTC(time)+","+str(Price[time])+","+str(Signal[time])+","+str(PnL)+"\n")
        csv_file.write(linuxToUTC(time)+","+str(Price[time])+","+str(Signal[time])+","+str(PnL)+"\n")
    csv_file.close()


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
t = threading.Timer(60.00, fetchServer2Data)
t.start()

Price = {}
Signal = {}
PnL = {}
Price = {}

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
        fetchServer1Data()
        fetchServer2Data()
        exit(main(port))