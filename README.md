# ConfederatedApp
The idea is a generic base for applications that run a single instance across machines and across displays. (Think J.A.R.V.I.S.)

## The design:
* Machines announce themselves on the lan via zeroconf and/or upnp
* Each machine maintains its own websocket endpoint
* Document state is synched across each machine that has it open
* If a document is opened that last had windows open on another machine, those windows are all reopened

## Outstanding questions
* How to reliably keep document states in synch?
* How to resolve if documemt copies are not in synch?
* Could a tool like git be used to help with this?
* **CURRENTLY, THESE QUESTIONS ARE BEING IGNORED TO REDUCE PROBLEM SCOPE, BUT PROBABLY SHOULD INVESTIGATE LATER**

## Status
* This is currently only a loose conglomeration of parts.
    Many of them should be moved into other libraries.