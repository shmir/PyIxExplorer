
TGN - Traffic Generator
IXE - IxExplorer

This package implements Python OO API for Ixia IxExplorer traffic generator.


Functionality
The current version supports the following test flow:
	Build configuration -> Start/Stop traffic -> Get statistics.
Supported operations:
	- Load configuration - reserve ports and load configuration (prt or str)
	- Basic operations - get/set attributes, get/create children
	- Start/Stop - transmit, capture
	- Statistics - ports, streams and packet groups
	- Save configuration (prt or str)
	- Disconnect
The package also support Add/Remove objects so it supports the following test case:
	Load configuration -> Get/Set attributes -> Start/Stop traffic -> Get statistics.
But this is less elaborated and documented at this version.

TODO
Short term:
- Reset all stream sub commands to default when adding stream?
- Reset all port sub-commands when reseting port? 
- Stream (packet group) statistics
- Per port stream stats
- Set + set default automatically - not too much calls?
	add a global flag for automatic set or not 
	In case of True, the user will have to call the object's write function at the end
- Get specific list of counters instead of all
	Read_stats will get a list of stats to get, or empty == read all - Medium

Architecture:
- session is static object.
- Full documentation
- Full regression with tox, covarage etc.

Longer term:
- Should we clear stats on start traffic?
- Refine set_attributes for port etc - IxeObjectWithWrite?
- Use statList command?
- Local Tcl
- Full support for Linux server (including error detection)
- Better error messages
	- Test if Tcl server and chassis on the same version
	- add proper exception regarding miss match on multi server\chassis version
- Implicit load configuration
- Get/Set Enums
- Full support for Linux clients (over sockets only)
- Improve stream stats - performance, single stream only, set implicitly
- Load cfg

Installation:
stable - pip instsll ixeooapi

Prerequisite:
In case of Linux IxOS - IxExplorer application installed.

Related works:
The low level API of the package is based on python-ixia package - https://github.com/kontron/python-ixia.

Contact:
Feel free to contact me with any question or feature request at yoram@ignissoft.com
