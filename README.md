Palabre 
======

Palabre is a server written in pyton that opens a TCP port and allows you to connect in realtime from multiple clients and exchange informations.

Features : 
* XML based communication
* IRC style logic
* Connect
* Set Nickname
* Private message between two clients
* Creation of rooms
* Plugins for ... whatever you want
* ...

You have two options, just test palabre ... or install it.

## Testing Palabre
To test just run QuickStarter.py
```shell
python QuickStarter.py
```
or 
```shell
./QuickStarter.py
```


## Installing Palabre

To install it cleanly :
```bash
python setup.py install
```
Then edit `/etc/palabre.conf`

and start it 

`palabre start`

to stop it 

`palabre stop`

By default, log file is  `/var/log/palabre.log`
And scripts in `/usr/lib/python2.[VERSION]/site-packages/palabre/`


## XML example :
(By default if you try to connect with telnet, end of line is 'null' character for flash  not \n)



### Connection with nickname
```html
SENT : <connect nickname="KoolBoy"   />
```

### Answer from the server (nickname in use or non acceptable)
```html
RECEIVED : <connect isok="1"  />
```
### If you want to check the connection
```html
SENT : <ping  />
```
### The server should answer :
```html
RECEIVED : <pong  />
```
### Asking for room list
```html
SENT : <getrooms  />
```
### Rooms list (also supports sub-rooms, operator mode for some clients in rooms, params in rooms (title, locked, ...)
```html
RECEIVED : <rooms nb="2" ><room name="XXX" clients="5"   /><room clients="20" name="YYY"  /></rooms>
```
### Asking to join Room XXX (if room does not exists it is created then)
```html
SENT : <join room="XXX"  />
```
### Room Joined
```html
RECEIVED : <joined room="XXX"  />
```
### And the list of clients for this room
```html
RECEIVED : <clients room="XXX" nb="5" > <client name="Toto" /> <client name="Titi" /> [...]  </clients>
```
### Sending a message "msg" or "m"
### (Param "c" or "toclient" -> the message is only delivered to one client)
```html
SENT : <msg toclient="Nickname">Hello Nickname !</msg>
```

### Rooms params :
* Param "r" or "toroom" is delivered to entire room
* Param "b" or "back" tells the server to send the same message back to the send
* Param "broadcast" sends to everyone

```html
SENT : <m r="XXX" >Hello everyone i'm very happy to join you all!</m>

RECEIVED : <m f="Toto" r="XXX">Hello KoolBoy glad to meet you!</m>

SENT : <m f="Titi" r="XXX">Hi how are you KoolBoy ?</m>

SENT : <m r="XXX" >Have to go ! Bye !</m>

RECEIVED :  <leave r="XXX" />
```

Then the others receives the updated client list ...