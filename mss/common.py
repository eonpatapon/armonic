import os
import sys
import logging
import logging.handlers
import json
import traceback

from mss.utils import ethernet_ifs

class NetworkFilter(logging.Filter):
    """Use this filter to add ip address of agent in log. Could be
    useful if we simultaneous use several agents.

    It add %(ip) formatter.

    Add this filter to a handler via addFilter method."""
    def filter(self, record):
        try:
            record.ip = ethernet_ifs()[0][1]
        except IndexError:
            record.ip = ""
        return True

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

format = '%(asctime)s|%(levelname)7s - %(message)s'
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(format))

format = '%(asctime)s|%(name)20s|%(levelname)6s: %(message)s'
fh = logging.handlers.RotatingFileHandler("/tmp/mss.log", maxBytes=10485760, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(format))

logger.addHandler(ch)
logger.addHandler(fh)


def log_disable_stdout():
    logger.removeHandler(ch)

EVENT_LEVELV_NUM = 25
logging.addLevelName(EVENT_LEVELV_NUM, "EVENT")
def event(self, kws):
    # This level is used in mss to log an event.
    self._log(EVENT_LEVELV_NUM, kws, [], extra={"event_data": kws})
logging.Logger.event = event


PROCESS_LEVELV_NUM = 24
logging.addLevelName(PROCESS_LEVELV_NUM, "PROCESS")
def process(self, dct, *args, **kws):
    """This level permits to log the output of processes. In fact, the
    message is transmitted only if it contains a '\n' otherwise, it is
    buffered until the next '\n'."""
    if not hasattr(self,"_processline"):
        self._processline = ""
    t = dct.split("\n")
    if len(t) == 1:
        self._processline+=t[0]
    elif len(t) > 1:
        self._log(PROCESS_LEVELV_NUM, self._processline + t[0], args, **kws)
        for i in t[1:-1]:
            self._log(PROCESS_LEVELV_NUM, i, args, **kws)
        if t[-1] != '':
            self._processline = t[-1]
        else :
            self._processline = ""
logging.Logger.process = process


def expose(f):
    "Decorator to set exposed flag on a function."
    f.exposed = True
    return f


def is_exposed(f):
    "Test whether another function should be publicly exposed."
    return getattr(f, 'exposed', False)


def load_lifecycles(dir,include_modules=None):
    """Import Lifecycle modules from dir"""
    if os.path.exists(os.path.join(dir, '__init__.py')):
        sys.path.insert(0, dir)
        for module in os.listdir(dir):
            if (include_modules is not None
                and module not in include_modules):
                continue
            if os.path.exists(os.path.join(dir, module, '__init__.py')):
                try:
                    __import__(module)
                    logger.info("Imported module %s" % module)
                except ImportError as e:
                    logger.info("Module %s can not be imported" % module)
                    logger.debug("Exception on import module %s:" % module)
                    tb=traceback.format_exc().split("\n")
                    for l in tb:
                        logger.debug("  %s"%l)


class DoesNotExist(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, msg, require_name=None, variable_name=None):
        Exception.__init__(self,msg)
        self.variable_name = variable_name
        self.require_name = require_name

    def __setstate__(self,dict):
        self.variable_name = dict['variable_name']
        self.require_name = dict['require_name']

    def __repr__(self):
        return "Variable '%s' of require '%s' is required!" % (self.variable_name, self.require_name)

    def __str__(self):
        return self.__repr__()

class ProvideError(Exception):
    def __init__(self, lf_name, state_name, provide_name, msg):
        self.lf_name=lf_name
        self.state_name=state_name
        self.provide_name=provide_name
        self.msg=msg
        Exception.__init__(self, "%s.%s.%s : %s" % (lf_name, state_name, provide_name, msg))

    def __reduce__(self):
        """We need to override it to support pickle. Must be FIXED."""
        return (ProvideError, (self.lf_name, self.state_name, self.provide_name, self.msg, ))


class IterContainer(list):
    """
    Simple object container

    Is an iterator to loop over objects:
        objects = IterContainer(*objects)
        for object in objects:
            print object.name, object.value

    And provide easy way to retrieve objects
    that have a name attribute:

        objects = IterContainer(*objects)
        object = objects.object_name
        print object.name, object.value
        object = objects.get("object_name")
        print object.name, object.value

    """
    def __init__(self, *args):
        super(IterContainer, self).__init__([arg for arg in args])
        for arg in args:
            if hasattr(arg, 'name'):
                self.__setattr__(arg.name, arg)

    def get(self, attr):
        if hasattr(self, attr):
            return getattr(self, attr)
        raise DoesNotExist("%s does not exist" % attr)


