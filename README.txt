
+++ WORK IN PROGRESS - only API and basic pyixia objects are fully functional. +++

TGN - Traffic Generator
IXE - IxExplorer

This package implements Python OO API for Ixia IxExplorer traffic generator.

Todo:
Short term:
- Add port statistics counters
- Stream (packet group) statistics
- Start/Stop/Retrieve capture

Longer term:
- Local Tcl
- Get/Set attribute
- Fully adjust to other TG packages
	- remove id/port_id/stream_id etc and replace with obj_name()/obj_ref()/obj_parent() etc.
- Support UTG
- Load from remote machine on socket API (copy to shared location)?

Installation:
stable - pip instsll ixeooapi
testing - pip install ixeooapi -r --extra-index-url https://testpypi.python.org/pypi

Prerequisite:
In case of Linux IxOS - IxExplorer application installed.

Related works:
The low level API of the package is based on python-ixia package - https://github.com/kontron/python-ixia.

Contact:
Feel free to contact me with any question or feature request at yoram@ignissoft.com
