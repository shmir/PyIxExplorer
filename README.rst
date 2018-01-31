
TGN - Traffic Generator
IXE - IxExplorer

This package implements Python OO API for Ixia IxExplorer traffic generator.

Functionality
"""""""""""""
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

Prerequisite:
"""""""""""""
Access to IxTclServer connected to IxServer. IxTclServer can run on any Windows machine as long as it can aceess the
IxServer of the requested chassis.

Installation:
"""""""""""""
stable - pip instsll pyixexplorer

Getting started
"""""""""""""""
Under ixexplorer.test.ixe_samples you will shows basic samples (under development).
Additional code snippets can be found in ixexplorer.test.test*
See inside for more info.

Related works:
""""""""""""""
The low level API of the package is based on python-ixia package - https://github.com/kontron/python-ixia.

Contact:
""""""""
Feel free to contact me with any question or feature request at yoram@ignissoft.com
