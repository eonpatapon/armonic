class Remote(object):
    def __init__(self):
        self.provides = []

    @classmethod
    def from_json(cls, dct_json, child_num):
        this = cls()
        this.child_num = child_num
        this.xpath = dct_json['xpath']
        this.type = dct_json['type']
        this.nargs = dct_json['nargs']
        this.provide_xpath = dct_json['provide_xpath']
        this.provide_args = dct_json['provide_args']
        return this

def build_require_from_call_require(dct_json):
    acc = []
    idx = 0
    for p in dct_json:
        for require in p['requires']:
            if require['type'] in ['external', 'local']:
                acc.append(Remote.from_json(require, child_num=idx))
                idx += 1
    return acc
                

class Provide(object):
    """

    :param child_number: if this Provide is a dependancies, this is
    the number of this child.
    :param requirer: the provide that require this require
    :param require: the require of the requirer
    """
    STEPS = ["manage", 
             "lfm",
             "specialize",
             "set_dependancies",
             # This is a private step
             "multiplicity", 
             #"prepare_requires",
             "call",
             "done"]

    def __init__(self, generic_xpath, requirer=None, child_num=None, require=None):
        self.generic_xpath = generic_xpath
        self.requirer = requirer
        self.require = require
        
        if requirer is not None:
            self.depth = requirer.depth + 1
            self.tree_id = []
            for i in requirer.tree_id:
                self.tree_id.append(i)
            self.tree_id.append(child_num)
                
            
        else:
            self.depth = 0
            self.tree_id = [0]

        self.ignore = False
        self._step_current = 0

        self._current_require = None
        self._children_generator = None

        # Provide configuration variables.
        #
        # If this provide comes from a local require, the lfm is taken
        # from the requirer.
        if ((require is not None and 
             require.type == "local")):
            self._lfm = requirer.lfm
        else:
            self._lfm = None

        self._manage = None
        self._call = None
            
    def has_requirer(self):
        return self.requirer is not None
 
    @property
    def step(self):
        return Provide.STEPS[self._step_current]
        
    def _next_step(self):
        if self._step_current+1 > len(Provide.STEPS)-1:
            raise IndexError
        self._step_current += 1
        
    def build_requires(self):
        provides = self.lfm.provide_call_requires(self.specialized_xpath)
        #pprint(self.lfm.provide_call_args(provide.specialized_xpath))
        self._requires = []
        self.remotes = build_require_from_call_require(provides)
                    
    def requires(self):
        """Be careful, this function always returns the same generator."""
        def c():
            for r in self.remotes:
                yield r
        
        if self._children_generator is None:
            self._children_generator = c()
           
        return self._children_generator

    def build_child(self, generic_xpath, child_num, require):
        ret = self.__class__(generic_xpath=generic_xpath, 
                             requirer=self,
                             child_num=child_num,
                             require=require)
        return ret

    @property
    def lfm(self):
        """If it returns None, walk function yields."""
        return self._lfm
        
    @lfm.setter
    def lfm(self, lfm):
        self._lfm = lfm

    @property
    def manage(self):
        """If it returns None, walk function yields."""
        return self._manage
        
    @manage.setter
    def manage(self, manage):
        """Set true if this provide has to be managed"""
        self._manage = manage
        # Used to stop the genreator
        self.ignore = not manage

    @property
    def call(self):
        """If it returns None, walk function yields."""
        return self._call
        
    @call.setter
    def call(self, call):
        """Set true if this provide has to be called"""
        self._call = call

    def matches(self):
        """Return the list of xpaths that matched the generic_xpath"""
        return self.lfm.uri(xpath=self.generic_xpath)

    def specialize(self, xpath):
        """Used to specialize the generic_xpath"""
        self.specialized_xpath = xpath
    
    def lfm_call(self):
        self.provide_ret = self.lfm.provide_call(
            xpath=self.specialized_xpath,
            requires={},
            provide_args={})


def walk(root_scope):
    """Return a generator which 'yields' a 3-uple (provide, step,
    optionnal_args)."""

    scope = root_scope
    while True:
        # Stop and Pop conditions
        if scope.step == "done":
            yield (scope, scope.step, None)
        if scope.step == "done" or scope.ignore:
            # If all dependencies of root node have been threated we
            # break the loop
            if scope.requirer == None:
                break
            # If all dependencies have been threated we
            # go back to its requirer.
            else:
                scope = scope.requirer
                continue

        if not scope.ignore:
            if scope.step == "manage":
                if scope.manage is None: 
                    scope.manage = yield (scope, scope.step, None)
                scope._next_step()

            elif scope.step == "lfm":
                if scope.lfm is None:
                    scope.lfm = yield(scope, scope.step, None)
                scope._next_step()

            elif scope.step == "set_dependancies":
                scope.build_requires()
                #yield(scope, scope.step, None)
                scope._next_step()

            elif scope.step == "call":
                if scope.call is None:
                    scope.call = yield(scope, scope.step, None)
                if scope.call:
                    scope.lfm_call()
                scope._next_step()

            elif scope.step == "specialize":
                m = scope.matches()
                if len(m) > 1:
                    specialized = yield(scope, scope.step, m)
                else:
                    specialized = m[0]
                scope.specialize(specialized)
                scope._next_step()

            elif scope.step == "multiplicity":
                if scope._current_require is None:
                    # For each require, provides are built
                    try:
                        # Get the next require to manage
                        req = scope.requires().next()
                        req.provides = []
                        if req.nargs == "*":
                            number = yield (scope, scope.step, req)
                            for i in range(0,number):
                                req.provides.append(scope.build_child(
                                    generic_xpath=req.provide_xpath, 
                                    child_num=req.child_num,
                                    require=req))
                        else:
                            req.provides.append(scope.build_child(
                                generic_xpath=req.provide_xpath, 
                                child_num=req.child_num,
                                require=req))
                        scope._current_require = req
                    except StopIteration:
                        pass

                    # If all requires have been treated, the
                    # manage_dependancies step is done
                    if scope._current_require is None:
                        scope._next_step()
                       
                else:
                    done = True
                    for p in scope._current_require.provides:
                        if p.ignore == False and not p.step == "done":
                            done = False
                            scope = p
                            break
                    if done:
                        scope._current_require = None
            else: 
                yield (scope, scope.step, None)
                scope._next_step()

