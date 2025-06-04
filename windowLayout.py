"""
Keep track of window layouts across machines
"""
import typing
from stringTools import yntf
from machineIdentity import MachineIdentity,localMachineIdentity
from jsonHelper import JsonBase,JsonCompatible,asJson,JsonLike


class WindowLayout(JsonBase):
    """
    Layout applied to a single window
    """
    def __init__(self,
        jsonObj:typing.Optional[JsonCompatible]=None):
        """ """
        self.name:str=''
        self.size:typing.Tuple[int,int]
        self.location:typing.Tuple[int,int]
        self.minimized:bool
        self.maximized:bool
        if jsonObj is not None:
            self.jsonObj=asJson(jsonObj)

    @property
    def jsonObj(self)->JsonLike:
        """
        get/set this as a json object
        """
        return {
            'name':self.name,
            'size':asJson(self.size),
            'location':asJson(self.location),
            'minimized':str(self.minimized),
            'maximized':str(self.maximized)
        }
    @jsonObj.setter
    def jsonObj(self,jsonObj:JsonLike):
        """
        get/set this as a json object
        """
        self.name=jsonObj.get('name','')
        self.size=tuple(jsonObj.get('size',(640,480)))
        self.location=tuple(jsonObj.get('location',(0,0)))
        self.minimized=yntf(jsonObj.get('minimized','t'))
        self.maximized=yntf(jsonObj.get('maximized','t'))


class DisplayLayout(JsonBase):
    """
    Layout applied to a single window
    """
    def __init__(self,
        jsonObj:typing.Optional[JsonCompatible]=None):
        """ """
        self.name:str=''
        self.windows:typing.Dict[str,WindowLayout]
        if jsonObj is not None:
            self.jsonObj=asJson(jsonObj)

    @property
    def jsonObj(self)->JsonLike:
        """
        get/set this as a json object
        """
        return {
            'name':self.name,
            'windows':asJson(self.windows)
        }
    @jsonObj.setter
    def jsonObj(self,jsonObj:JsonLike):
        """
        get/set this as a json object
        """
        self.name=jsonObj.get('name','')
        self.windows={}
        for k,v in jsonObj.get('windows',{}).items():
            self.windows[k]=MachineLayout(v)


class DesktopLayout(JsonBase):
    """
    Layout applied to a single window
    """
    def __init__(self,
        jsonObj:typing.Optional[JsonCompatible]=None):
        """ """
        self.name:str=''
        self.displays:typing.Dict[str,DisplayLayout]
        if jsonObj is not None:
            self.jsonObj=asJson(jsonObj)

    @property
    def jsonObj(self)->JsonLike:
        """
        get/set this as a json object
        """
        return {
            'name':self.name,
            'displays':asJson(self.displays)
        }
    @jsonObj.setter
    def jsonObj(self,jsonObj:JsonLike):
        """
        get/set this as a json object
        """
        self.name=jsonObj.get('name','')
        self.displays={}
        for k,v in jsonObj.get('displays',{}).items():
            self.displays[k]=MachineLayout(v)


class MachineLayout(JsonBase):
    """
    Layout applied to a single window
    """
    def __init__(self,
        jsonObj:typing.Optional[JsonCompatible]=None):
        """ """
        self.identity:MachineIdentity
        self.desktops:typing.Dict[str,DesktopLayout]
        if jsonObj is not None:
            self.jsonObj=asJson(jsonObj)

    @property
    def name(self)->str:
        """
        Name of this machine
        """
        return str(self.identity)

    @property
    def jsonObj(self)->JsonLike:
        """
        get/set this as a json object
        """
        return {
            'name':self.name,
            'desktops':asJson(self.desktops)
        }
    @jsonObj.setter
    def jsonObj(self,jsonObj:JsonLike):
        """
        get/set this as a json object
        """
        self.identity=jsonObj.get('name','')
        self.desktops={}
        for k,v in jsonObj.get('desktops',{}).items():
            self.desktops[k]=MachineLayout(v)

    def __repr__(self):
        return str(self.identity)


class ConfederatedAppLayout(JsonBase):
    """
    Layout applied to distributed application instance
    """
    def __init__(self,
        jsonObj:typing.Optional[JsonCompatible]=None):
        """ """
        self.machines:typing.Dict[MachineIdentity,MachineLayout]
        if jsonObj is not None:
            self.jsonObj=asJson(jsonObj)

    @property
    def localMachine(self):
        """
        Get the window layout for ourselves
        """
        return self.machines[localMachineIdentity]

    @property
    def remoteMachines(self)->typing.Generator[MachineLayout,None,None]:
        """
        All of the machines besides this one
        """
        for identity,machine in self.machines.items():
            if identity!=localMachineIdentity:
                yield machine

    @property
    def jsonObj(self)->JsonLike:
        """
        get/set this as a json object
        """
        return {
            'machines':asJson(self.machines)
        }
    @jsonObj.setter
    def jsonObj(self,jsonObj:JsonLike):
        """
        get/set this as a json object
        """
        self.machines={}
        for k,v in jsonObj.get('machines',{}).items():
            self.machines[k]=MachineLayout(v)
