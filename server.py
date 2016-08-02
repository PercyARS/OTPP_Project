#!/usr/bin/env python
# server.py
 
import socket
import select
import Queue
import threading
from threading import *
import urllib
import urllib2
import sys
import gzip
import time
import datetime
import numpy as np
from collections import OrderedDict
import SocketServer


# class object that encapsulates data per minute

SERVER_TIME_OUT = 10


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
                # block for 1 second
                client, data = q.get(block=True, timeout=1)
                process(client, data)
            except Queue.Empty:
                # waiting for requests
                #sys.stdout.write('.')
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
    command = value.split(" ")[0]
    if command == "Reset":
        ret = Reset()
    elif command == "Price":
        ret = getPrice(float(value.split(" ")[1]))
    elif command == "Signal":
        ret = getSignal(int(value.split(" ")[1]))
    else:
        print "Bad request received: " + value
        return
    try:
        print ("Server sending: "+ret)
        client.sendall(ret)
    except socket.error, msg:
        print "Server failed to reply, Socket error! %s" % msg

def Reset():
    # reset csv file data and all internal data structure
    Price = OrderedDict()
    Signal = OrderedDict()
    PnL = OrderedDict()
    fetchServer1Data()
    return "OK"


def getPrice(time):
    # if client needs most recent time
    if time == 0:
        return str(Price.values()[-1])
    else:
        if time in Price.keys():
            return str(Price[time])
        else:
            return "NO"


def getSignal(time):
    # if client needs most recent time
    if time == 0:
        return str(Signal.values()[-1])
    else:
        if time in Signal.keys():
            return str(Signal[time])
        else:
            return "NO"

# fetch tick data every minute
def fetchServer2Data_Live():
    #called every minute
    data = urllib2.urlopen("https://api.bitcoinaverage.com/history/USD/per_minute_24h_sliding_window.csv")
    PriceWindow = []
    firstLine = True
    for line in data:
        if firstLine:
            firstLine = False
            continue
        time = line.split(",")[0]
        time1 = time.split(" ")[0]
        time2 = time.split(" ")[1]
        time = time1+"-"+time2
        # get rid of second
        time1 = time.split(":")[0]
        time2 = time.split(":")[1]
        time = time1+":"+time2
        time = UTCtoLinux(time)
        price = float(line.split(",")[1])
        Price[time] = price
        PriceWindow.append(price)

    # updating the internal data structure
    # now time points to the latest time
    print "Adding Server2 data at:" + linuxToUTC(time) + " Price" + str(price)
    calculateTradingStrategies(PriceWindow,time)

def linuxToUTC(linuxTime):
    return datetime.datetime.fromtimestamp(int(linuxTime)).strftime('%Y-%m-%d-%H:%M')

def UTCtoLinux(UTCString):
    return int(time.mktime(datetime.datetime.strptime(UTCString,"%Y-%m-%d-%H:%M").timetuple())-14400)

def lastSignal(time):
    for i in range(len(Signal.keys()))[::-1]:
        if Signal.keys()[i] < time:
            break
    return Signal[Signal.keys()[i]]

def lastPrice(time):
    for i in range(len(Price.keys()))[::-1]:
        if Price.keys()[i] < time:
            break
    return Price[Price.keys()[i]]

def calculateTradingStrategies(PriceWindow, time):
    S_avg = {}
    Sigma = {}
    S_avg[time] = np.mean(PriceWindow)
    Sigma[time] = np.std(PriceWindow)
    # calculate signal and price of last minute's data

    _lastSignal = lastSignal(time)
    _lastPrice = lastPrice(time)
    if Price[time] > S_avg[time] + Sigma[time]:
        Signal[time] = 1
    elif Price[time] < S_avg[time] - Sigma[time]:
        #print ("need to sell")
        Signal[time] = -1
    else:
        Signal[time] = 0
    # calculate P&L
    PnL[time] = _lastSignal * (Price[time]/_lastPrice-1)

def fetchServer1Data():
    print 'Reading Server1 Data...'
    #dataFile = urllib.URLopener()
    #dataFile.retrieve('http://api.bitcoincharts.com/v1/csv/bitfinexUSD.csv.gz', "past.csv.gz")
    csv_file = open("Server1Result.csv", "w")
    csv_file.write("datetime, price, signal, pnl\n")
    HourWindow = []
    with gzip.open('past1.csv.gz','rt') as f:
        for line in f:
            PriceWindow = []
            time1 = int(line.split(",")[0])
            # find the closest minute
            time = time1 - time1 % 60
            price = float(line.split(",")[1])
            Price[time] = price
            # the time of first entry
            firstDataTime = Price.keys()[0]
            Signal[firstDataTime] = 0
            # if there is not enough entries for the window
            if time <= firstDataTime + 86400:
                pass
            # there are enough elements to calculate the window
            else:
                startTime = time - 86400
                i = 0
                while HourWindow[i] < startTime:
                    HourWindow.remove(HourWindow[i])
                    i += 1
            # append to the 24 hour time window
            HourWindow.append(time)
            # extract the price
            for i in HourWindow:
                PriceWindow.append(Price[i])
            calculateTradingStrategies(PriceWindow,time)
    print 'Writing price and trading strategies to file: Server1Result.csv'
    for time in Signal.keys():
        #print ("Time:"+linuxToUTC(time))
        #print ("Writing:"+linuxToUTC(time)+","+str(Price[time])+","+str(Signal[time])+","+str(PnL[time])+"\n")
        csv_file.write(linuxToUTC(time)+","+str(Price[time])+","+str(Signal[time])+","+str(PnL[time])+"\n")
    print "Reading finished"
    csv_file.close()


class MyTCPHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        print "New connection from: " + self.client_address[0]
        while True:
            data = self.request.recv(4096)
            print ("We got request: "+ data)
            p.add((self.request, data))



def main(port):
    host = socket.gethostname()
    server = SocketServer.TCPServer(("localhost", port), MyTCPHandler)
    try:
        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.serve_forever()
    except KeyboardInterrupt:
        print "Ctrl-c hit, Stop."
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
Price = OrderedDict()
Signal = OrderedDict()
PnL = OrderedDict()

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
        t = threading.Timer(60.00, fetchServer2Data_Live)
        t.start()
        fetchServer2Data_Live()
        exit(main(port))