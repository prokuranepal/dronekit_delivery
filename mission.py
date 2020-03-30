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

def save_mission(vehicle):
    """
    Save a mission in the Waypoint file format
    (http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).
    """
    missionlist=[]
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    #output='QGC WPL 110\n'
    for cmd in cmds:
        missionlist.append(cmd)

    #Add file-format information

    #Add home location as 0th waypoint
    waypoint={}

    home=vehicle.home_location
        #print(home.lat,home.lon,home.alt)
    waypoint[0]={
    'lat':home.lat,
    'lng':home.lon,
    
    }
        #Add commands
    inc=1
    for cmd in missionlist:
        if cmd.command!=22:
            waypoint[inc]= {
            'lat': cmd.x,
            'lng': cmd.y,
            'alt': cmd.z,
            'command': cmd.command
            }
            inc=inc+1

    return waypoint
