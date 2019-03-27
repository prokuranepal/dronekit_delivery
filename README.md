# dronekit_delivery
This repo contains code to establish a socket connection with server by which an android app can retrieve drone data as well as send commands like RTL, takeoff, land, upload missions to drone.
* The main code is sendData.py which establishes socket communication with the server to enable communication with client via android app.
* drone.service is a systemd service program to start sendData.py on bootup of companion computer, ie. raspberry pi. It needs to be copied to /etc/system/systemd folder and the service needs to be  enabled and started.
