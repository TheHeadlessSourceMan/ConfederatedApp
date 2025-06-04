"""
Determine what device we are talking about
"""
import typing
from jsonHelper import JsonBase,asJson,JsonCompatible


class NetworkLocation(JsonBase):
    """
    Network host and port
    """
    def __init__(self,
        host:str,
        port:int,
        jsonObj:typing.Optional[typing.Dict[str,typing.Any]]=None):
        """ """
        self.host=host
        self.port=port
        if jsonObj is not None:
            self.jsonObj=jsonObj

    @property
    def jsonObj(self)->typing.Dict[str,typing.Any]:
        """
        get/set this as a json object
        """
        ret={
            'host':self.host,
            'port':self.port}
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.host=jsonObj.get('host','')
        self.port=jsonObj.get('port',0)

    def __repr__(self):
        return f'{self.host}:{self.port}'


class MachineIdentity(JsonBase):
    """
    Determine what device we are talking about
    """
    def __init__(self,
        userName:str,
        machineName:str,
        operatingSystem:str,
        machineType:str,
        networkLocation:typing.Optional[NetworkLocation]=None,
        jsonObj:typing.Optional[JsonCompatible]=None):
        """ """
        self.userName=userName
        self.machineName=machineName
        self.operatingSystem=operatingSystem
        self.machineType=machineType
        self.networkLocation=networkLocation
        if jsonObj is not None:
            self.jsonObj=asJson(jsonObj)

    @property
    def jsonObj(self)->typing.Dict[str,typing.Any]:
        """
        get/set this as a json object
        """
        ret={
            'userName':self.userName,
            'machineName':self.machineName,
            'operatingSystem':self.operatingSystem,
            'machineType':self.machineType}
        if self.networkLocation is not None:
            ret['networkLocation']=self.networkLocation
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.userName=jsonObj.get('userName','[UNKNOWN]')
        self.machineName=jsonObj.get('machineName','[UNKNOWN]')
        self.operatingSystem=jsonObj.get('operatingSystem','[UNKNOWN]')
        self.machineType=jsonObj.get('machineType','[UNKNOWN]')
        networkLocation=jsonObj.get('networkLocation')
        if networkLocation is None:
            self.networkLocation=None
        else:
            self.networkLocation=NetworkLocation('',0,jsonObj=networkLocation)

    def __repr__(self):
        if self.networkLocation:
            return f'{self.userName} on {self.machineType} {self.machineName}({self.operatingSystem}) listening on {self.networkLocation}' # noqa: E501 # pylint: disable=line-too-long
        return f'{self.userName} on {self.machineType} {self.machineName}({self.operatingSystem})' # noqa: E501 # pylint: disable=line-too-long


def getLocalMachineType()->str:
    """
    Utility to figure out what type the running computer is
    eg, "Laptop", "Desktop", "Tablet", or "Phone"

    If it can't figure it out, it simply says "computer"

    See also:
        https://devblogs.microsoft.com/scripting/how-can-i-determine-if-a-computer-is-a-laptop-or-a-desktop-machine/
        https://stackoverflow.com/questions/62817340/check-if-running-on-laptop-or-desktop-chassis-type-in-python
    """
    return "computer"


localMachineIdentity:MachineIdentity=None
def getLocalDeviceIdentity()->MachineIdentity:
    """
    Get the local device identity
    """
    global localMachineIdentity
    if localMachineIdentity is None:
        import platform
        import getpass
        user=getpass.getuser()
        uname=platform.uname()
        osName=f'{uname[0]} {uname[1]}'
        machineType=getLocalMachineType()
        localMachineIdentity=MachineIdentity(user,uname[1],osName,machineType)
    return localMachineIdentity
localDeviceIdentity=getLocalDeviceIdentity()
