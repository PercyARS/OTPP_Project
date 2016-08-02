__author__ = 'zhaopeix'

import socket
import traceback
import sys
import select
import time
import datetime
import smtplib


# create socket object
SERVER_TIME_OUT = 10
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def sendMail(msg):
    with open("EMAIL_CONFIG") as f:
        for line in f:
            type = line.split(":")[0]
            if type == "SenderAddress":
                fromaddr = line.split(":")[1]
            elif type == "SenderPassword":
                frompwd = line.split(":")[1]
            elif type == "ReceiverAddress":
                toaddr = line.split(":")[1]
            else:
                print "Invalid config file, sending failed"
                return
    if fromaddr == "" or frompwd == "" or toaddr == "":
        print "Config file is missing contents, sending failed"
        return
    print "Sending e-mail to: "+ toaddr
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (fromaddr, toaddr, "SERVER COMMUNICATION FAILED", msg)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(fromaddr, frompwd)
        #server.sendmail(fromaddr, toaddr, message)
        server.close()
        #print 'Successfully sent the mail'
    except:
        print "Failed to send mail"



def processConnect():
    address = raw_input("What is the server's IP address? Press Enter if localhost is used\n")
    if address == "":
        address = "127.0.0.1"
    port = raw_input("What is the server's port number? Press Enter if 8000 is used\n")
    if port == "":
        port = 8000
    else:
        port = int(port)
    print "Connecting to: " + address + ":" + str(port)
    try:
        s.connect((address, port))
        # set as non blocking socket
        s.setblocking(0)
        print "Connection successful"
    except socket.error, msg:
        print "Connection error: %s" %msg
        sendMail(msg)

def processReset():
    try:
        s.sendall("Reset ")
        # set it to blocking for reset request only
        s.setblocking(1)
        # keep on waiting until hear back from server
        data = s.recv(4096)
        if data == "OK":
            print "Reset successful, exit now"
            exit(0)
        else:
            print "Reset failed, exit now"
            exit(1)
    except socket.error, msg:
        print "Reset failed, Socket error! %s" % msg
        sendMail(msg)
        exit(1)


def UTCtoLinux(UTCString):
    return int(time.mktime(datetime.datetime.strptime(UTCString,"%Y-%m-%d-%H:%M").timetuple())-14400)

def processSignal():
    date = raw_input("Signal at which minute, enter UTC time in this format: YYYY-MM-DD-HH:MM or press enter if most "
                     "recent signal is required")
    # if the user entered nothing, print NOW
    if date == "":
        date = "NOW"
        # send 0 to server if now is needed
        time = 0
    else:
        try:
            time = UTCtoLinux(date)
        except ValueError, msg:
            print "Invalid format" %msg
            return

    try:
        print ("Sending: Signal "+ str(time))
        s.sendall("Signal "+ str(time))
        ready = select.select([s], [], [], SERVER_TIME_OUT)
        if ready[0]:
            data = s.recv(4096)
            if data == "NO":
                print "No signal data available for: " + date
            else:
                print "Signal at " + date + " is: " + data
        else:
            msg = "Server not responding"
            print msg
            sendMail(msg)
    except socket.error, msg:
        print "Asking signal failed, Socket error! %s" % msg
        sendMail(msg)


def processPrice():
    date = raw_input("Price at which minute, enter UTC time in this format: YYYY-MM-DD-HH:MM or press enter if most "
                     "recent price is required")
    # if the user entered nothing, print NOW
    if date == "":
        date = "NOW"
        # send 0 to server if now is needed
        time = 0
    else:
        try:
            time = UTCtoLinux(date)
        except ValueError, msg:
            print "Invalid format" %msg
            return

    try:
        print ("Sending: Price "+ str(time))
        s.sendall("Price "+ str(time))
        ready = select.select([s], [], [], SERVER_TIME_OUT)
        if ready[0]:
            data = s.recv(4096)
            if data == "NO":
                print "No price data available for: " + date
            else:
                print "Price at " + date + " is: " + data
        else:
            msg = "Server not responding"
            print msg
            sendMail(msg)
    except socket.error, msg:
        print "Asking price failed, Socket error! %s" % msg
        sendMail(msg)


if __name__ == "__main__":
    try:
        while True:
            input_command = raw_input('===========================\nChoose one of the following numbers:'
                                      '\n1. Connect\n2. Reset\n3. Price\n4. Signal\n===========================\n')

            if input_command == "1":
                processConnect()
            elif input_command == "2":
                processReset()
            elif input_command == "3":
                processPrice()
            elif input_command == "4":
                processSignal()
            else:
                print "Invalid choice, try again"
    except KeyboardInterrupt:
        print "Ctrl-c hit, Stop."
        exit(0)





