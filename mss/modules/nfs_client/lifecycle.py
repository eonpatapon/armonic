from mss.lifecycle import State, Transition, Lifecycle, provide
from mss.require import Require, RequireExternal
from mss.variable import Port, VString
import mss.state

import mss.common
import logging
logger=logging.getLogger(__name__)

class NotInstalled(State):pass
class Installed(mss.state.InstallPackagesUrpm):
    packages=["nfs-client"]

class Active(State):
    services=["nfs-client"]
    
    @RequireExternal("Nfs", "get_dir", provide_ret = [VString("remotetarget")])
    @Require([VString("path")], name="mountpoint")
    def get_dir(self, requires):
        mountpoint = requires.get("mountpoint").variables.path.value
        remotetarget = requires.get("Nfs.get_dir").variables.remotetarget.value
        logging.info("mount.nfs %s %s" % (remotetarget, path))

class Nfs_client(Lifecycle):
    transitions=[
        Transition(NotInstalled()    ,Installed()),
        Transition(Installed()      ,Active()),
        ]

    def __init__(self):
        self.init(NotInstalled(),{})
