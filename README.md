# pyqsys

## Description
This is an attempt to create a Python library to communicate with QSYS QSC Cores or the QSYS Designer in emulation mode over their QRC (JSONRPC 2.0) protocol.
The aim of this project is to provide a high level interface while also exposing the bare QRC methods. 

## Dependencies
-  [jsonrpcclient](https://github.com/explodinglabs/jsonrpcclient)

## Status

- [x] Bare QRC methods
- [ ] High level interface

## How to install

```pip install jsonrpcclient pyqsys```

## Usage
Create a Core object and just call the methods with the correct [arguments](https://q-syshelp.qsc.com/#External_Control_APIs/QRC/QRC_Commands.htm).

```python
from pyqsys import Core

core = Core("192.168.0.135")
core.connect()

# If you need to log on to your QSC core use
core.logon("username", "password")

# Request status message
core.status_get()

# Get a names and values of all controls of a component
core.Component.get_controls(component_name)

# Load snapshot
core.Snapshot.load(bank_name, bank_number, ramp)
```

## References
- [QRC API Reference](https://q-syshelp.qsc.com/#External_Control_APIs/QRC/QRC_Commands.htm)
- Inspired by [https://github.com/gagehelton/qsys](https://github.com/gagehelton/qsys)
