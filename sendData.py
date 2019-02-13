from __future__ import print_function
from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative
import arm_takeoff as arm
import datetime
import math
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
magcal_progess = []
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

def read_username_password():
    d={}
    r=0
    file = open('pyfile.txt', 'r')
    for line in file:
    	d[r]=line.split("\n")[0]
    	r=r+1
    return d

try:
    socket1 = SocketIO('http://192.168.1.81', 3000, verify=True) #establish socket connection to desired server
    #socket1 = SocketIO('https://nicwebpage.herokuapp.com', verify =True)
    socket = socket1.define(BaseNamespace,'/JT603')
    #socket.emit("joinPiPulchowk")
    socket.emit("joinPi")
    #socket.emit("usernamePassword",read_username_password())
except Exception as e:
    print('The server is down. Try again later.')

def set_mode_LAND(var):
    fix_type=0
    try:
        fix_type=vehicle.gps_0.fix_type
    except Exception as e:
        pass
    if fix_type >1:
        vehicle.mode=VehicleMode("LAND")
        print ("Vehicle mode set to LAND")

def set_mode_RTL(var):
    fix_type=0
    try:
        fix_type=vehicle.gps_0.fix_type
    except Exception as e:
        pass
    if fix_type >1:
        vehicle.mode=VehicleMode("RTL")
        print ("Vehicle mode set to RTL")

waypoint={}
def on_mission_download(var): #this function is called once the server requests to download the mission file, to send mission to server
    print("DOWNLOAD MISSION COMMAND BY USER",var)
    missionlist=[]
    inc=0
    missionlist=up.download_mission(vehicle)
    for cmd in missionlist:
        if cmd.command!=22:
            waypoint[inc]= {
            'lat': cmd.x,
            'lng': cmd.y,
            'alt': cmd.z,
            'command': cmd.command
            }
            inc=inc+1
    if bool(waypoint):#checking if the mission file has been downloaded from pixhawk
        socket.emit('waypoints',waypoint)
        print("Mission downloaded by user")
        print (str(waypoint))
    else:
        error={'context':'GPS/Mission','msg':'GPS error OR no mission file received!!'}
        socket.emit("errors",error)

def update_mission(var):
    try:
        up.upload_mission(vehicle,'/home/sa/mission/'+str(var))
        print (str(var), "loaded")
    except Exception as e:
        error={'context':'GPS/Mission','msg':'Mission FIle Could not be loaded'}
        socket.emit("errors",error)


flight_checker=False #to check that the fly command is given successfully only once
def on_initiate_flight(var):
    global flight_checker #reuired global, as this is a socket funciton, got no idea how to pass parameters to socket function
    try:
        height =vehicle.location.global_relative_frame.alt
        if vehicle.is_armable and height <= 4: # and not flight_checker: #checking if vehicle is armable and fly command is genuine
            socket.emit("success","flight_success")
            print("FLIGHT INITIATED BY USER")
            arm.arm_and_takeoff(vehicle,4) #arm and takeoff upto 4 meters
            vehicle.mode = VehicleMode("AUTO") #switch vehicle mode to auto
            # flight_checker=True ## True if succesful flight, no further flight commands will be acknowledged
            flight_checker=True
        else:
            fix_type=0
            try:
                fix_type=vehicle.gps_0.fix_type
            except Exception as e:
                pass
            if fix_type > 1:
                vehicle.mode=VehicleMode("AUTO")
                print ("Vehicle mode set to AUTO")


    except Exception as e:
        #print(e)
        error={'context':'Prearm','msg':'Pre-arm check failed!!!'}
        socket.emit("errors",error)

# Get all vehicle attributes (state)
print("\nGet all vehicle attribute values:")


def send_data(threadName, delay):
    global waypoint #needs to be global as it is accessed by on_mission_download, socket function
    checker=False #flag to start the functions to calculate total distance and eta once the mission is received from pixhawk
    total=0
    check = True
    divisor=1
    last_vel=0
    data = {}
   
    # magcal(vehicle)
    while 1:
        # print("data sending ")
        try:
            loc = vehicle.location.global_frame
        except Exception as e:
            error={'context':'loc','msg':'Location not found!!!'}
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
            data["lat"] = format(loc.lat,'.15f')
            data["lng"] = format(loc.lon,'.15f')
        except Exception as e:
            error={'context':'format','msg':'Long lat format error!!!'}
            socket.emit("errors",error)
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
            data["arm"] = vehicle.armed
        except Exception as e:
            error={'context':'arm','msg':'Arm not found!!!'}
            socket.emit("errors",error)
        try:
            data["ekf"] = vehicle.ekf_ok
        except Exception as e:
            error={'context':'ekf','msg':'ekf not found!!!'}
            socket.emit("errors",error)
        try:
            data["mode"] = vehicle.mode.name
        except Exception as e:
            error={'context':',mode','msg':'Mode not found!!!'}
            socket.emit("errors",error)
        try:
            data["alt"] = format(loc.alt, '.2f')
        except Exception as e:
            error={'context':'alt','msg':'altitude format error!!!'}
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
        try:
            data["altr"] = vehicle.location.global_relative_frame.alt
        except Exception as e:
            error={'context':'altr','msg':'rel alt not found!!!'}
            socket.emit("errors",error)
        try:
            data["head"] = format(vehicle.heading, 'd')
        except Exception as e:
            error={'context':'head','msg':'head not found!!!'}
            socket.emit("errors",error)
        try:
            data["as"]=format(vehicle.airspeed, '.3f')
        except Exception as e:
            error={'context':'as_format','msg':'as format error!!!'}
            socket.emit("errors",error)
        try:
            data["lidar"] = vehicle.rangefinder.distance
        except Exception as e:
            error={'context':'lidar','msg':'Lidar not found!!!'}
            socket.emit("errors",error)
        try:
            data["gs"] = format(vehicle.groundspeed, '.3f')
        except Exception as e:
            error={'context':'gs','msg':'gs format error!!!'}
            socket.emit("errors",error)
        try:
            data["status"] = status[13:]
        except Exception as e:
            error={'context':'status','msg':'status not found!!!'}
            socket.emit("errors",error)
        try:
            data["volt"] = format(vehicle.battery.voltage, '.2f')
        except Exception as e:
            error={'context':'volt','msg':'voltage not found!!!'}
            socket.emit("errors",error)


        # print(datetime.datetime.now())
        if  checker:#only if waypoints are successfully read

            if vehicle.armed and check: # check is used to receive time of arming only once, at first arming
                time1 = datetime.datetime.now() #receive time once armed
                check=False
            if not check :
                try:
                    time2 = datetime.datetime.now()# calculate current time
                    flight_time=float((time2-time1).total_seconds()) # calculate total flight time
                    vel=float((last_vel+vehicle.groundspeed)/divisor) #calculate the average velocity upto current time
                    est=float((float(total)-flight_time*vel)/3.5) #estimate eta, with assummed velocity 3.5 m/s
                    if est<=0.5: #making sure eta is not less thatn 0.5
                        est=0
                    data["est"]=est
                    last_vel+=vehicle.groundspeed #summing up velcity to average them
                    divisor+=1 # the number of values of velocity
                except Exception as e:
                    pass

        socket.emit('data',data) #send data to server
        socket.on('mission_download',on_mission_download) #keep listening for download command for mission from server
        socket.on('initiate_flight',on_initiate_flight)#keep listening for fly command from user
        print(data["head"])
        try:
            socket.on('positions',update_mission)
        except Exception:
            print ("error positions")
        try:
            socket.on('RTL',set_mode_RTL)
        except Exception:
            pass
        try:
            socket.on('magcal',magcal_start)
        except Exception:
            pass
        try:
            socket.on('LAND',set_mode_LAND)
        except Exception:
            pass
        if vehicle.gps_0.fix_type > 1   and not checker: ## check gps before downloading the mission as home points are not received without gps, and checker to download mission only once
            try:
                waypoint=mi.save_mission(vehicle) # call the save mission function which downloads the mission from pixhawk and arranges waypoints into a dictionary
                print("MISSION DOWNLOADED")
                total=dis.calculate_dist(waypoint) # calculate total distance between home and final waypoint
                socket.emit('homePosition',waypoint[0]) # send homePosition to server as soon as gps lock
                checker=True # switch value of checker such that mission is downloaded only once from pixhawk, and condition to calculate eta is met
            except Exception as e:
                print(e)
                print("GPS error OR no mission file received!!!")
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
         
start()

while True:
    pass
