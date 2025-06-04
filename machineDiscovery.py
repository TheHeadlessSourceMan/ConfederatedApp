"""
Tools to locate other machines that are also
running instances of this confederated application.
"""
import typing
from machineIdentity import localDeviceIdentity,NetworkLocation,MachineIdentity
from remoteApi import queryMachineIdentity


ApplicationIdentity=str
MachineAddedCallback=typing.Callable[[MachineIdentity],None]
MachineRemovedCallback=typing.Callable[[MachineIdentity],None]


class MachineDisoveryManager:
    """
    Announces this application to the network and
    tracks when other machines with the application
    are added/removed

    NOTE: will only notify callbacks of applications
    on machines that it is paired with.
    """
    def __init__(self,
        applicationIdentity:ApplicationIdentity,
        networkLocation:NetworkLocation,
        onMachineAddedCallbacks:typing.Optional[
            typing.Iterable[MachineAddedCallback]]=None,
        onMachineRemovedCallbacks:typing.Optional[
            typing.Iterable[MachineRemovedCallback]]=None):
        """ """
        self._machines:typing.Dict[str,MachineIdentity]={}
        self.applicationIdentity=applicationIdentity
        self.announce(networkLocation)
        self.onMachineAddedCallbacks:typing.List[MachineAddedCallback]=\
            list(onMachineAddedCallbacks)
        self.onMachineRemovedCallbacks:typing.List[MachineRemovedCallback]=\
            list(onMachineRemovedCallbacks)

    @property
    def serviceIdentity(self)->str:
        """
        Convert the application name into a service name
        """
        return 'confederatedApplication.'+self.applicationIdentity

    def announce(self,
        networkLocation:NetworkLocation):
        """
        Announce to the network that this confederated app is here

        (This will be announced automatically when class starts.
        Only need to call this manually if the network location changes.)
        """
        localDeviceIdentity.networkLocation=networkLocation
        upnp.announce(str(networkLocation),self.serviceIdentity)
        zeroconf.annunce(str(networkLocation),self.serviceIdentity)

    def refresh(self):
        """
        find all machines running this application
        """
        updatedMachineList=set([
            machine.address for machine in zeroconf.find(self.serviceIdentity)])
        updatedMachineList.union([
            machine.address for machine in upnp.find(self.serviceIdentity)])
        # check for new machines added
        for address in updatedMachineList:
            if address not in self._machines:
                machine=queryMachineIdentity(address)
                if machine:
                    self._machines[address]=machine
                    for fn in self.onMachineAddedCallbacks:
                        fn(machine)
        # check for old machines removed
        for address,machine in self._machines:
            if address not in updatedMachineList:
                for fn in self.onMachineRemovedCallbacks:
                    fn(machine)
