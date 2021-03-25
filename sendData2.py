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
from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative, Command
import arm_takeoff as arm
import datetime
import math
import threading
import json
import time
from pymavlink import mavutil
from socketIO_client_nexus import SocketIO, BaseNamespace
import mission as mi
import distance as dis
#Set up option parsing to get connection string
import argparse
import upload_mission as up
import unittest


# parser = argparse.ArgumentParser(description='Print out vehicle state information. Connects to SITL on local PC by default.')
# parser.add_argument('--connect',
#                   help="vehicle connection target string. If not specified, SITL automatically started and used.")
# args = parser.parse_args()

# connection_string = args.connect
# print("\nConnecting to vehicle on: %s" , connection_string)

# vehicle = connect(connection_string, wait_ready=True)

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

# Connect to the Vehicle..
#   Set `wait_ready=True` to ensure default attributes are populated before `connect()` returns.
print("\nConnecting to vehicle on: %s" % connection_string)
vehicle = connect(connection_string, wait_ready=True)
vehicle.wait_ready('autopilot_version')
magcal_progess = []




def download_mission():
    """
    Download the current mission from the vehicle.
    """
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready() # wait until download is complete.




def add_mission(mission_waypoints, speed):
    """
    Adds a takeoff command and four waypoint commands to the current mission. 
    The waypoints are positioned to form a square of side length 2*aSize around the specified LocationGlobal (aLocation).
    The function assumes vehicle.commands matches the vehicle mission state 
    (you must have called download at least once in the session and after clearing the mission)
    """	
    print ("waypoint", mission_waypoints)
    try:
        cmds = vehicle.commands

        print(" Clear any existing commands")
        cmds.clear() 
        
        print(" Define/add new commands.")
        # Add new commands. The meaning/order of the parameters is documented in the Command class. 
        
        #Add MAV_CMD_NAV_TAKEOFF command. This is ignored if the vehicle is already in the air.
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 0, 10))

        #Define the four MAV_CMD_NAV_WAYPOINT locations and add the commands
        for i in range(len(mission_waypoints)):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, mission_waypoints[i]["lat"], mission_waypoints[i]["lng"],float(mission_waypoints[i]["altitude"])))
        print(" Upload new commands to vehicle")
        cmds.upload()
    except Exception as e:
        print("failed to upload mission")



def set_servo(vehicle, servo_number, pwm_value):
    pwm_value_int = int(pwm_value)
    msg = vehicle.message_factory.command_long_encode(0, 0,mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,servo_number,pwm_value_int,0,0,0,0,0)
    vehicle.send_mavlink(msg)

def magcal_start():
    msg = vehicle.message_factory.command_long_encode(0,0,mavutil.mavlink.MAV_CMD_DO_START_MAG_CAL,0,0,0,1,0,0,0,0)
    vehicle.send_mavlink(msg)
    print('magcal started')

def accelcal():
    msg = vehicle.message_factory.command_long_encode(0, 0, mavutil.mavlink.MAV_CMD_PREFLIGHT_CALIBRATION,0,0, 0, 0, 0, 1, 0, 0)
    vehicle.send_mavlink(msg)
      
def magaccept():
    msg = vehicle.message_factory.command_long_encode(0, 0,mavutil.mavlink.MAV_CMD_DO_ACCEPT_MAG_CAL, 0, 0, 0, 1,0,0,0,0)
    vehicle.send_mavlink(msg)
    error={'context':'magcal','msg':'magcal successful'}
    socket.emit("errors",error) 
    print ("magcal accepted")
# print (dir(vehicle.message_factory))

# magcal(vehicle)
# time.sleep(120)
#set_servo(vehicle,9,1500)
magcal_progess = []

# def read_username_password():
#     d={}
#     r=0
#     file = open('pyfile.txt', 'r')
#     for line in file:
#     	d[r]=line.split("\n")[0]
#     	r=r+1
#     return d

socket1 = SocketIO('http://9a5d0aed70c4.ngrok.io', verify =True)
socket = socket1.define(BaseNamespace,'/JT603')
while not socket._connected:
    socket1 = SocketIO('http://9a5d0aed70c4.ngrok.io', verify =True)
    socket = socket1.define(BaseNamespace,'/JT603')
socket.emit("joinDrone",'5fa2839a9827ab1a65bf2cd8')

# try:
#     #socket1 = SocketIO('http://10.42.0.200', 3000, verify=True) #establish socket connection to desired server
#     #socket1 = SocketIO('http://drone.nicnepal.org', verify=True) #establish socket connection to desired server
#     socket1 = SocketIO('https://nicwebpage.herokuapp.com', verify =True)
#     socket = socket1.define(BaseNamespace,'/JT601')
#     #socket = socket1.define(BaseNamespace,'/pulchowk')
#     #socket.emit("joinPiPulchowk")
#     socket.emit("joinPi")
#     #socket.emit("usernamePassword",read_username_password())
# except Exception as e:
#     print('The server is down. Try again later.')

def set_mode_LAND(var):
    fix_type=0
    try:
        fix_type=vehicle.gps_0.fix_type
    except Exception as e:
        print (str(e))
    print("LAND command received")
    if fix_type >1:
        while(vehicle.mode.name!="LAND"):
            vehicle.mode=VehicleMode("LAND")
            print ("Vehicle mode set to LAND")       
    return vehicle.mode.name


def set_mode_RTL(var):
    fix_type=0
    try:
        fix_type=vehicle.gps_0.fix_type
    except Exception as e:
        print(str(e))
    print("RTL command received")
    if fix_type >1:
        vehicle.mode=VehicleMode("RTL")
        print ("Vehicle mode set to RTL")
        while(vehicle.mode.name!="RTL"):
            pass
    return vehicle.mode.name

waypoint={}
checker=False
def on_mission_download(var): #this function is called once the server requests to download the mission file, to send mission to server
    print("DOWNLOAD MISSION COMMAND BY USER",var)
    mission_all={}
    missionlist=[]
    missionList2=[]
    inc=0

    missionlist=up.download_mission(vehicle)
    for cmd in missionlist:
        if cmd.command!=22 and cmd.command!=3000 and cmd.command!=183 :
            print ("mission File ","cmd X", cmd.x,"cmd Y", cmd.y, cmd.command)
            waypoint[inc]= {
            'lat': cmd.x,
            'lng': cmd.y,
            'altitude': cmd.z,
            'action': cmd.command
            }
            missionList2.append(waypoint[inc])
            inc=inc+1

    if bool(waypoint):#checking if the mission file has been downloaded from pixhawk
        mission_all['waypoints']=missionList2
        socket.emit('getMission',mission_all)
        print("Mission downloaded by user", mission_all)
        print (str(waypoint))
    else:
        error={'context':'GPS/Mission','msg':'GPS error OR no mission file received!!'}
        socket.emit("errors",error)
    return waypoint 
def update_mission(var):
    global checker
    print("mission",var)
    add_mission(var["mission"]['waypoints'],7)
    # try:
    #     up.upload_mission(vehicle,str(var))
    #     print (str(var), "loaded")
    #     checker=False
    #     print("checker",checker)
    # except Exception as e:
    #     error={'context':'GPS/Mission','msg':'Mission FIle Could not be loaded'}
    #     socket.emit("errors",error)
    # return checker 

def on_reconnect():
    socket.emit("joinDrone")

# flight_checker=False #to check that the fly command is given successfully only once
def on_initiate_flight(var):
    print("flight command received")
    # global flight_checker #required global, as this is a socket funciton, got no idea how to pass parameters to socket function
    try:
        height =vehicle.location.global_relative_frame.alt
        if vehicle.is_armable and height <= 4: # and not flight_checker: #checking if vehicle is armable and fly command is genuine
            socket.emit("success","flight_success")
            print("FLIGHT INITIATED BY USER")
            #arm.arm_and_takeoff(vehicle,4) #arm and takeoff upto 4 meters
            # Copter should arm in GUIDED mode
            vehicle.mode    = VehicleMode("GUIDED")
            # vehicle.armed   = True
            # # Confirm vehicle armed before attempting to take off
            # while not vehicle.armed:
            #     print (" Waiting for arming...")
            #     time.sleep(1)
            # arm.arm_and_takeoff(vehicle,4) #arm and takeoff upto 4 meters
            # while(vehicle.mode.name!="AUTO"):
            #     vehicle.mode = VehicleMode("AUTO") #switch vehicle mode to auto
            # # flight_checker=True ## True if succesful flight, no further flight commands will be acknowledged
            print("FLIGHT INITIATED BY USER")
            arm.arm_and_takeoff(vehicle,4) #arm and takeoff upto 4 meters
            vehicle.mode = VehicleMode("AUTO") #switch vehicle mode to auto	
            # flight_checker=True ## True if succesful flight, no further flight commands will be acknowledged
            # flight_checker=True
            #UNCOMMENT FOR PLANE TAKEOFF
            # vehicle.mode    = VehicleMode("GUIDED")
            # vehicle.armed   = True
            # # Confirm vehicle armed before attempting to take off
            # while not vehicle.armed:
            #     print (" Waiting for arming...")
            #     time.sleep(1)
            # vehicle.mode = VehicleMode("AUTO") #switch vehicle mode to auto'''
            # flight_checker=True
        else:
            fix_type=0
            try:
                fix_type=vehicle.gps_0.fix_type
            except Exception as e:
                pass
            if fix_type > 1:
                while(vehicle.mode.name!="AUTO"):
                    vehicle.mode=VehicleMode("AUTO")
                print ("Vehicle mode set to AUTO")


    except Exception as e:
        #print(e)
        error={'context':'Prearm','msg':'Pre-arm check failed!!!'}
        socket.emit("errors",error)
    return vehicle.mode.name, vehicle.armed

# Get all vehicle attributes (state)

def send_home(var):
    print("homePosition",homePos)
    if homePos:
        socket.emit("homePosition",homePos)

def send_data():
    global waypoint #needs to be global as it is accessed by on_mission_download, socket function
    global checker #flag to start the functions to calculate total distance and eta once the mission is received from pixhawk
    total=0
    check = True
    flight_flag=False
    divisor=1
    last_vel=0
    servo_flag=False
    data = {}
    global homePos
    # magcal(vehicle)
    a =0
    loc=0
    while True:
    # while a<=30:    
        a=a+1
        # print("data sending ")
        try:
            loc = vehicle.location.global_frame
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)
        try:
            data["lat"] = format(loc.lat,'.15f')
            data["lng"] = format(loc.lon,'.15f')
        except Exception as e:
            error={'context':'format','msg':'Long lat format error!!!'}
            socket.emit("errors",error)
        try:
            data["altr"] = vehicle.location.global_relative_frame.alt
        except Exception as e:
            error={'context':'altr','msg':'rel alt not found!!!'}
            socket.emit("errors",error)
        try:
            data["alt"] = format(loc.alt, '.2f')
        except Exception as e:
            data["alt"] =0
            error={'context':'alt','msg':'altitude format error!!!'}
            socket.emit("errors",error)
        try:
            data["numSat"] = vehicle.gps_0.satellites_visible
        except Exception as e:
            error={'context':'numSat','msg':'numSat not found!!'}
            socket.emit("errors",error)
        try:
            data["hdop"] = vehicle.gps_0.eph
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)
        try:
            data["fix"] = vehicle.gps_0.fix_type
        except Exception as e:
            error={'context':'fix','msg':'fix type not found!!!'}
            socket.emit("errors",error)

        try:
            data["head"] = format(vehicle.heading, 'd')
        except Exception as e:
            error={'context':'head','msg':'head not found!!!'}
            socket.emit("errors",error)
        try:
            data["gs"] = format(vehicle.groundspeed, '.3f')
        except Exception as e:
            error={'context':'gs','msg':'gs format error!!!'}
            socket.emit("errors",error)
        try:
            data["as"]=format(vehicle.airspeed, '.3f')
        except Exception as e:
            error={'context':'as_format','msg':'as format error!!!'}
            socket.emit("errors",error)
        try:
            data["mode"] = vehicle.mode.name
        except Exception as e:
            error={'context':',mode','msg':'Mode not found!!!'}
            socket.emit("errors",error) 
        try:
            data["ekf"] = vehicle.ekf_ok
        except Exception as e:
            error={'context':'ekf','msg':'ekf not found!!!'}
            socket.emit("errors",error)
        try:
            status = str(vehicle.system_status)
            data["status"] = status[13:]
        except Exception as e:
            error={'context':'status','msg':'status not found!!!'}
            socket.emit("errors",error)
        try:
            data["lidar"] = vehicle.rangefinder.distance
        except Exception as e:
            error={'context':'lidar','msg':'Lidar not found!!!'}
            socket.emit("errors",error)
        try:
            data["volt"] = format(vehicle.battery.voltage, '.2f')
        except Exception as e:
            error={'context':'volt','msg':'voltage not found!!!'}
            socket.emit("errors",error)
        try:
            data["arm"] = vehicle.armed
        except Exception as e:
            error={'context':'arm','msg':'Arm not found!!!'}
            socket.emit("errors",error)    
        data["est"] = 0

        try:
            vel = vehicle.velocity
        except Exception as e:
            error={'context':'vel','msg':'velocity not found!!!'}
            socket.emit("errors",error)
        try:
            status = str(vehicle.system_status)
        except Exception as e:
            error={'context':'status','msg':'Status not found!!!'}
            socket.emit("errors",error)
        try:
            data["conn"] = 'True'
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
            socket.emit("errors",error)



        try:
            data["roll"] = vehicle.attitude.roll
        except Exception as e:
            error={'context':'roll','msg':'roll not found!!!'}
            socket.emit("errors",error)
        try:
            data["pitch"] = vehicle.attitude.pitch
        except Exception as e:
            error={'context':'pitch','msg':'pitch not found!!!'}
            socket.emit("errors",error)
        try:
            data["yaw"] = vehicle.attitude.yaw
        except Exception as e:
            error={'context':'yaw','msg':'yaw not found!!!'}
            socket.emit("errors",error)

        # print(data["head"],datetime.datetime.now().strftime("%H:%M:%S")) #use this for monitoring status
        # print(data["head"],datetime.datetime.now())
        # print(data["head"],datetime.datetime.now())
        try:
            if vehicle.commands.next >= 6 and servo_flag == False:
                servo_flag=True
                socket.emit('payloadDrop',1)
                print("package dropped iosndfidnsf sdif nsianfo nasfoidn saoifnoid snafiodnsoaifniosdaniofgnsdaiogndsiognipasndgpimsadpogmsapogpodsamgopdsmgpomsdapogmsapodmgposmadgpo!")
        except Exception as e:
            pass
        try:
            if vehicle.armed and vehicle.location.global_relative_frame.alt >= 5 and not flight_flag:
                socket.emit("flight_start", 1)
                flight_flag=True
                print("mission started, drone on its way",loc.alt)
        except Exception as e:
            pass
    
        try:
            if not vehicle.armed and flight_flag:
                socket.emit("flight_start",0)
                print("mission completed")
                flight_flag=False
        except Exception as e:
            pass
        if not vehicle.armed:
            time1=0
        # print(datetime.datetime.now())
        if checker: #only if waypoints are successfully read
            if vehicle.armed and check: # check is used to receive time of arming only once, at first arming
                time1 = datetime.datetime.now() #receive time once armed
                check=False
            if not check:
                try:
                    time2 = datetime.datetime.now()# calculate current time
                    flight_time=float((time2-time1).total_seconds()) # calculate total flight time
                    vel=float((last_vel+vehicle.groundspeed)/divisor) #calculate the average velocity upto current time
                    print (flight_time, total)
                    est=float((float(total)-flight_time*vel)/3.5) #estimate eta, with assummed velocity 3.5 m/s
                    print("est",est)
                    if est<=0.5: #making sure eta is not less thatn 0.5
                        est=0
                    data["est"]=est
                    last_vel+=vehicle.groundspeed #summing up velcity to average them
                    divisor+=1 # the number of values of velocity
                except Exception as e:
                    pass
        socket.emit('data',data) #send data to server
        # print("data", data)
        socket.on('homePosition',send_home)
        socket.on('getMission',on_mission_download) #keep listening for download command for mission from server
        socket.on('initiateFlight',on_initiate_flight)#keep listening for fly command from user
        try:
            socket.on('mission',update_mission)
        except Exception:
            print ("error positions")
        try:
            socket.on('rtl',set_mode_RTL)
        except Exception:
            pass
        try:
            socket.on('magcal',magcal_start)
        except Exception:
            pass
        try:
            socket.on('land',set_mode_LAND)
        except Exception:
            pass
        socket.on('reconnect', on_reconnect)
        if vehicle.gps_0.fix_type > 1 and not checker: ## check gps before downloading the mission as home points are not received without gps, and checker to download mission only once
            try:
                mission_file=[ { "altitude": 0, "radius": 0, "action": 'takeoff', "lat": -35.36346217651667, "lng": 149.16542374267578},{"altitude": '20', "radius": '20', "action": 'waypoint',  "lat": -35.36826217651367,  "lng": 149.1682374267528},{  "altitude": 0,  "radius": 0,  "action": 'land',  "lat": -35.33326217651067,  "lng": 149.1612374267578}]
                add_mission(mission_file,20)
                waypoint=mi.save_mission(vehicle) # call the save mission function which downloads the mission from pixhawk and arranges waypoints into a dictionary
                print("MISSION DOWNLOADED")
                total=dis.calculate_dist(waypoint) # calculate total distance between home and final waypoint
                print("total distance",waypoint,total)
                homePos=waypoint[0]
                socket.emit('homePosition',waypoint[0]) # send homePosition to server as soon as gps lock
                checker=True # switch value of checker such that mission is downloaded only once from pixhawk, and condition to calculate eta is met
            except Exception as e:
                print(e)
                print("GPS error(fix type<0) OR no mission file received!!!")
        socket1.wait(seconds=0.2) #sends or waits for socket activities in every seconds specified
                #socket.wait()

def start(): #to perform all the operations in a thread
    try:
        print("inside start")
        thread.start_new_thread(send_data,("Send Data", 1)) # function, arguments
        #save_mission()
        #calculate_dist()
    except Exception as e:
        error={'context':'thread','msg':'thread error!!!'}
        socket.emit("errors",error)

number_of_compass=[]
no_comp=[]

@vehicle.on_message('*')
def listener(self, name, message):
    global no_comp
    global number_of_compass
    if message.get_type() == 'MAG_CAL_PROGRESS':
        comp_id=message.compass_id
        if comp_id not in number_of_compass:
            number_of_compass.append(comp_id)
        print (message.compass_id,message.completion_pct)  
        #completed='compass '+str(message.compass_id)+': ' +str(message.completion_pct)+ '% completed'
        #error={'context':'magcal','msg':completed}
        #socket.emit("errors",error)    
    if message.get_type() == 'MAG_CAL_REPORT':
        if message.cal_status == mavutil.mavlink.MAG_CAL_SUCCESS:
            comp_id2=message.compass_id
            if comp_id2 not in no_comp:
                no_comp.append(comp_id2)
        else:
            print("Mag cal failed")
        if  set(number_of_compass)== set(no_comp) and len(number_of_compass)!=0 and len(no_comp)!=0:
            magaccept()
            del number_of_compass[:]
            del no_comp[:]
    if message.get_type() =='STATUSTEXT':
        if message.text=='flight plan received':
            error={'context':'android','msg':str(message.text)}     
        else:
            error={'context':'STATUS','msg':str(message.text)}
        socket.emit("errors",error)
        print (message.text)
         
# class TestSocketIO(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         pass


#     def setUp(self):
#         pass

#     def tearDown(self):
#         pass

    # def test_connect(self):
    #     client = socket1.define(BaseNamespace,'/JT602')
    #     client2= socket1.define(BaseNamespace,'/JT603')
    #     self.assertTrue(client._connected)
    #     self.assertIsNotNone(client)
    #     self.assertIsNotNone(client2)
    #     self.assertNotEqual(client, client2)
    #     # data =1
    #     # p =client.on_message(data)
    #     # print (p)
    #     # received = client.get_received()
    #     # self.assertEqual(len(received), 3)
    #     # self.assertEqual(received[0]['args'], 'connected')
    #     # self.assertEqual(received[1]['args'], '{}')
    #     # self.assertEqual(received[2]['args'], '{}')
    #     # client.disconnect()
    #     # self.assertFalse(client._connected)
    #     # self.assertTrue(client2._connected)
    #     # client2.disconnect()
    #     # self.assertFalse(client2.is_connected)

def on_connect(var):
    print ("hello var",var)

if __name__ == '__main__':    
    # unittest.main() 
    send_data()
    


# f= datetime.datetime.now()
# while datetime.datetime.now()-f<=60:
#     pass

# time.sleep(80)
