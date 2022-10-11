[![Python 3.7|3.8|3.9](https://img.shields.io/badge/python-3.7%7C3.8%7C.3.9%7C.3.10-blue.svg)](https://www.python.org/downloads/release/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Python OO API for Ixia IxExplorer traffic generator.

Functionality
---
The current version supports the following test flow:

- Build configuration -> Start/Stop traffic -> Get statistics.

Supported operations:

- Load configuration - reserve ports and load configuration (prt or str)
- Basic operations - get/set attributes, get/create children
- Start/Stop - transmit, capture
- Statistics - ports, streams and packet groups
- Save configuration (prt or str)
- Disconnect

The package also support Add/Remove objects so it supports the following test case:
- Load configuration -> Get/Set attributes -> Start/Stop traffic -> Get statistics.
But this is less elaborated and documented at this version.

Prerequisite:
---
Access to IxTclServer connected to IxServer. IxTclServer can run on any Windows machine as long as it can aceess the
IxServer of the requested chassis.

Installation:
---
```bash
pip install pyixexplorer
```

Getting started
---
Under ixexplorer.samples.ixe_samples you will find basic samples.

Related works:
---
The low level API of the package is based on python-ixia package - https://github.com/kontron/python-ixia.

Contact
---
Feel free to contact me with any question or feature request at [yoram@ignissoft.com](mailto:yoram@ignissoft.com).
