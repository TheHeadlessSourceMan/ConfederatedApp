"""
This wraps the .appplicationIdenty/pairedMachines.json file
in the user's home directory
"""
import typing
from pathlib import Path
from authentication import authenticateMachine
from machineIdentity import MachineIdentity


class PairedMachines:
    """
    This wraps the .appplicationIdenty/pairedMachines.json file
    in the user's home directory
    """
    def __init__(self,applicationIdentity:str):
        """ """
        self.applicationIdentity=applicationIdentity
        self._pairedAuthKeys:typing.Dict[MachineIdentity,str]={}
        self.reload()

    @property
    def filename(self)->Path:
        """
        the .appplicationIdenty/pairedMachines.json file
        in the user's home directory
        """
        return Path.home()/f'.{self.applicationIdentity}'/'pairedMachines.json'

    def reload(self):
        """
        reload the .appplicationIdenty/pairedMachines.json file
        in the user's home directory
        """
        try:
            self.jsonStr=self.filename.read_text('utf-8',errors='ignore')
        except FileNotFoundError:
            self._pairedAuthKeys={}
            self.save()
    load=reload

    def save(self):
        """
        save to the .appplicationIdenty/pairedMachines.json file
        in the user's home directory
        """
        self.filename.write_text(self.jsonStr,'utf-8',errors='ignore')

    def addPairedMachine(self,
        machine:MachineIdentity,
        authenticationKey:str
        )->None:
        """
        Add a new machine to the paired list

        Generally, one would expect there to be a QR code on the host
        and then that shares the authenticationKey with the client

        This will also re-pair an existing device, in case the machine
        pairing has become invalid (eg, if they had to wipe a device)
        """
        # TODO: this file is not locked, so it could change on us
        self.reload()
        self._pairedAuthKeys[machine]=authenticationKey
        self.save()
    pair=addPairedMachine

    def isPairedAndAuthenticated(self,
        machine:MachineIdentity)->bool:
        """
        Determine if the machine is paired and authenticated
        """
        if machine in self._pairedAuthKeys:
            return authenticateMachine(machine,self._pairedAuthKeys[machine])
        return False
