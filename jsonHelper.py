"""
Tools for simplifiying json
"""
import typing
import os
from abc import abstractmethod
from pathlib import Path
import json


JsonLike=typing.Union[int,str,float,
    typing.List["JsonLike"],
    typing.Dict[str,"JsonLike"]]
JsonCompatible=typing.Union[str,JsonLike,"JsonBase"]
def asJsonObj(jsonCompatible:JsonCompatible)->JsonLike:
    """
    Attempt to get whatever is passed in as a Json-like "object"
    """
    if hasattr(jsonCompatible,'json'):
        return asJson(jsonCompatible.json)
    if isinstance(jsonCompatible,str):
        return json.loads(str)
    if isinstance(jsonCompatible,dict):
        fixed={}
        for k,v in jsonCompatible.items():
            fixed[str(k)]=asJson(v)
        return fixed
    if hasattr(jsonCompatible,'__iter__'):
        return [asJson(v) for v in jsonCompatible]
    return json.loads(str(JsonLike))
asJson=asJsonObj
def asJsonStr(jsonCompatible:JsonCompatible)->str:
    """
    Attempt to get whatever is passed in as a Json string
    """
    return json.dumps(asJson(jsonCompatible))

class JsonBase:
    """
    Helpful base class for objects with json data.

    Basically, you gain a whole lot of functionality
    just by defining a jsonObj getter/setter.
    """

    @property
    @abstractmethod
    def jsonObj(self)->JsonLike:
        """
        get/set this as a json object
        """
    @jsonObj.setter
    @abstractmethod
    def jsonObj(self,jsonObj:JsonLike):
        """
        get/set this as a json object
        """

    @property
    def jsonStr(self)->str:
        """
        get/set this as a json string
        """
        return json.dumps(self.jsonObj)
    @jsonStr.setter
    def jsonStr(self,jsonStr:str):
        """
        get/set this as a json string
        """
        self.jsonObj=json.loads(jsonStr)

    @property
    def json(self)->JsonLike:
        """
        get this as json-like data
        or set it based on anything JsonCompatible
        """
        return json.dumps(self.jsonObj)
    @json.setter
    def json(self,jsonCompatible:JsonCompatible):
        """
        get this as json-like data
        or set it based on anything JsonCompatible
        """
        self.jsonObj=asJson(jsonCompatible)

    def loadJson(self,path:typing.Union[str,Path])->None:
        """
        Load from json file
        """
        if not isinstance(path,Path):
            path=Path(os.path.expandvars(str(path)))
        data=path.read_text('utf-8',errors='ignore')
        self.jsonStr=data
    load=loadJson

    def saveJson(self,path:typing.Union[str,Path])->None:
        """
        Save to json file
        """
        if not isinstance(path,Path):
            path=Path(os.path.expandvars(str(path)))
        path.write_text(self.jsonStr,'utf-8',errors='ignore')
    save=saveJson

    def __repr__(self):
        return self.jsonStr
