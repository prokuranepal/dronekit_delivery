from __future__ import print_function
import arm_takeoff as arm
import datetime
import math
import threading
import json
import time
from socketIO_client_nexus import SocketIO, BaseNamespace
import mission as mi
import distance as dis
#Set up option parsing to get connection string
import argparse
import upload_mission as up

#parser = argparse.ArgumentParser(description='Print out vehicle state information. Connects to SITL on local PC by default.')
#parser.add_argument('--connect',
#                   help="vehicle connection target string. If not specified, SITL automatically started and used.")
#args = parser.parse_args()

#connection_string = args.connect
#print("\nConnecting to vehicle on: ,s" , connection_string)

#vehicle = connect(connection_string, wait_ready=True)d={}


try:
    #socket1 = SocketIO('http://192.168.1.100', 3000, verify=True) #establish socket connection to desired server
    #socket1 = SocketIO('http://drone.nicnepal.org', verify=True) #establish socket connection to desired server
    socket1 = SocketIO('https://nicwebpage.herokuapp.com', verify =True)
    socket = socket1.define(BaseNamespace,'/JT601')
    #socket = socket1.define(BaseNamespace,'/pulchowk')
    #socket.emit("joinPiPulchowk")
    socket.emit("joinPi")
    #socket.emit("usernamePassword",read_username_password())
except Exception as e:
    print('The server is down. Try again later.')


a=0

def send_data():
    global waypoint #needs to be global as it is accessed by on_mission_download, socket function
    global checker #flag to start the functions to calculate total distance and eta once the mission is received from pixhawk
    global a
    total=0
    check = True
    divisor=1
    last_vel=0
    data = {}
    # magcal(vehicle)
    while 1:
        # print("data sending ")
        try:
            data["altr"] = a
            a=a+1 
            print(a)
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)
        try:
            data["status"] = "standby"
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)
        try:
            data["mode"] = "auto"
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)
        try:
            data["conn"] = 'True'
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)
            datetime.datetime.now().strftime("%H:%M:%S")
        try:
            data["alt"] = datetime.datetime.now().strftime("%H:%M:%S")
            data["lat"] = str(float(85+float(a)/1000000))
            data["lng"] = str(float(27.7+float(a)/1000000))
            data["head"] = a
            data["hdop"] = a
        except Exception as e:
            error={'context':'numSat','msg':'numSat not found!!'}
            socket.emit("errors",error)
        try:
            data["hdop"] = datetime.datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)
        try:
            data["fix"] = datetime.datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            error={'context':'fix','msg':'fix type not found!!!'}
            socket.emit("errors",error)
        socket.emit('data',data) #send data to server
        socket1.wait(seconds=0.7)

def start(): #to perform all the operations in a thread
    try:
        print("inside start")
        thread.start_new_thread(send_data,("Send Data", 1)) # function, arguments
        #save_mission()
        #calculate_dist()
    except Exception as e:
        error={'context':'thread','msg':'thread error!!!'}
        socket.emit("errors",error)


         
send_data()

