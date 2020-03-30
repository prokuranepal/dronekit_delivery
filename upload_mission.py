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
from dronekit import connect, Command
import time


#Set up option parsing to get connection string


#Start SITL if no connection string specified



def readmission(vehicle,aFileName):
    #"""
    #Load a mission from a file into a list. The mission definition is in the Waypoint file
    #format (http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).

    #This function is used by upload_mission().
    #"""
    print( "\nReading mission from file: %s", aFileName)
    cmds = vehicle.commands
    missionlist=[]
    with open(aFileName) as f:
        for i, line in enumerate(f):
            if i==0:
                if not line.startswith('QGC WPL 110'):
                    raise Exception('File is not supported WP version')
            else:
                linearray=line.split('\t')
                ln_index=int(linearray[0])
                ln_currentwp=int(linearray[1])
                ln_frame=int(linearray[2])
                ln_command=int(linearray[3])
                ln_param1=float(linearray[4])
                ln_param2=float(linearray[5])
                ln_param3=float(linearray[6])
                ln_param4=float(linearray[7])
                ln_param5=float(linearray[8])
                ln_param6=float(linearray[9])
                ln_param7=float(linearray[10])
                ln_autocontinue=int(linearray[11].strip())
                cmd = Command( 0, 0, 0, ln_frame, ln_command, ln_currentwp, ln_autocontinue, ln_param1, ln_param2, ln_param3, ln_param4, ln_param5, ln_param6, ln_param7)
                missionlist.append(cmd)
    return missionlist

def upload_mission(vehicle,aFileName):
    """
    Upload a mission from a file. 
    """
    #Read mission from file
    missionlist = readmission(vehicle,aFileName)
    
    #Clear existing mission from vehicle
    print(' Clear mission')
    cmds = vehicle.commands
    cmds.clear()
    #Add new mission to vehicle
    for command in missionlist:
        cmds.add(command)
    print(' Upload mission')
    vehicle.commands.upload()



def download_mission(vehicle):
    
    #Downloads the current mission and returns it in a list.
    #It is used in save_mission() to get the file information to save.
    
    print (" Download mission from vehicle")
    missionlist=[]
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    for cmd in cmds:
        missionlist.append(cmd)
    return missionlist

def save_mission(vehicle,aFileName):
    
    #Save a mission in the Waypoint file format 
    #(http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).
   
    #Download mission from vehicle
    missionlist = download_mission()
    #Add file-format information
    output='QGC WPL 110\n'
    #Add home location as 0th waypoint
    home = vehicle.home_location
   # output+="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (0,1,0,16,0,0,0,0,home.lat,home.lon,home.alt,1)
    #Add commands
    for cmd in missionlist:
        commandline="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (cmd.seq,cmd.current,cmd.frame,cmd.command,cmd.param1,cmd.param2,cmd.param3,cmd.param4,cmd.x,cmd.y,cmd.z,cmd.autocontinue)
        output+=commandline
    with open(aFileName, 'w') as file_:
        print (" Write mission to file")
        file_.write(output)

