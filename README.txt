
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
1. Local Tcl
2. Full support for Linux server (including error detection)
3. Better error messages
4. Implicit load configuration
5, Get/Set Enums
6. Full support for Linux clients (over sockets only / with local Tcl)
7. Copy to file server
8. Set ports and streams for stream stats implicitly
9. Multi chassis
10. Elaborate Stats...
11. Load cfg
12. Copy pcap files from TG

Installation:
stable - pip instsll ixeooapi

Prerequisite:
In case of Linux IxOS - IxExplorer application installed.

Related works:
The low level API of the package is based on python-ixia package - https://github.com/kontron/python-ixia.

Contact:
Feel free to contact me with any question or feature request at yoram@ignissoft.com
