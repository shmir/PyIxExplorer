
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
- Stream (packet group) statistics

Longer term:
- Test if Tcl server and chassis on the same version
- Local Tcl
- Full support for Linux server (including error detection)
- Better error messages
- Implicit load configuration
- Get/Set Enums
- Full support for Linux clients (over sockets only)
- Copy files to (config) / from (cap) server
- Multi chassis
- Improve stream stats - performance, single stream only, set implicitly
- Load cfg
- Full documentation

Installation:
stable - pip instsll ixeooapi

Prerequisite:
In case of Linux IxOS - IxExplorer application installed.

Related works:
The low level API of the package is based on python-ixia package - https://github.com/kontron/python-ixia.

Contact:
Feel free to contact me with any question or feature request at yoram@ignissoft.com
