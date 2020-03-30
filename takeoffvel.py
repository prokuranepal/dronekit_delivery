'''

   This program is free software: you can redistribute it and/or modify

   it under the terms of the GNU General Public License as published by

   the Free Software Foundation, either version 3 of the License, or

   any later version.

   This program is distributed in the hope that it will be useful,

   but WITHOUT ANY WARRANTY; without even the implied warranty of

   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the

   GNU General Public License for more details.

   See LICENSE file in the project root for full license information./>.
'''
from __future__ import print_function
from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative
import arm_takeoff as arm
import datetime
import math as math
import threading
import json
import thread
import time
from pymavlink import mavutil
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

import argparse
parser = argparse.ArgumentParser(description='Print out vehicle state information. Connects to SITL on local PC by default.')
parser.add_argument('--connect',
                   help="vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

connection_string = args.connect
sitl = None

#Start SITL if no connection string specified
if not connection_string:
    import dronekit_sitl
    sitl = dronekit_sitl.start_default()
    connection_string = sitl.connection_string()

# Connect to the Vehicle.
#   Set `wait_ready=True` to ensure default attributes are populated before `connect()` returns.
print("\nConnecting to vehicle on: %s" % connection_string)
vehicle = connect(connection_string, wait_ready=True)
vehicle.wait_ready('autopilot_version')


def send_data(threadName, delay):
    # magcal(vehicle)
    arm_checker= True
    vehicle.parameters['THR_MIN']=0
    vehicle.armed=False
    takeoff_checker=True
    while 1:
        try:
            height =vehicle.location.global_relative_frame.alt
            vel = math.sqrt(vehicle.velocity[0]*vehicle.velocity[0]+vehicle.velocity[1]*vehicle.velocity[1]+vehicle.velocity[2]*vehicle.velocity[2])            
            #print(str(vel))
        except Exception as e:
            print("erro",str(e))
        if vehicle.is_armable and arm_checker: # and not flight_checker: #checking if vehicle is armable and fly command is genuine            vehicle.mode    = VehicleMode("GUIDED")
            vehicle.mode    = VehicleMode("GUIDED")
            vehicle.armed = True
            # Confirm vehicle armed before attempting to take off
            while not vehicle.armed:
                #print (" Waiting for arming...")
                time.sleep(1)    
            arm_checker=False
            #vehicle.parameters['THR_MIN']=100
        #print(vehicle.parameters['THR_MIN'])
        if vel >=3 and vehicle.armed:
            vehicle.mode = VehicleMode("AUTO")
            takeoff_checker=False
        if not takeoff_checker and vel<=1 and vehicle.armed:
            vehicle.armed=False
            while vehicle.armed:
                #print("waiting for disarming...")
                time.sleep(1)
        time.sleep(10)
        
      
def start(): #to perform all the operations in a thread
    try:
        print("inside start")
        thread.start_new_thread(send_data,("Send Data", 1)) # function, arguments
        #save_mission()
        #calculate_dist()
    except Exception as e:
        error={'context':'thread','msg':'thread error!!!'}
        
start()

while True:
    pass
