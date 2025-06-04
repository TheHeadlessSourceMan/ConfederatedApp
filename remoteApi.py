"""
Common commands to be run on a remote api
"""
from apiCommunication import ApiCommunication
from machineIdentity import MachineIdentity


def queryMachineIdentity(connection:ApiCommunication)->MachineIdentity:
    """
    Query the machine identity
    """
    json=connection.sendJsonMessage({'command':'queryMachineIdentity'})
    return MachineIdentity('','','','',None,json)
