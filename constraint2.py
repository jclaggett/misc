from functools import partial

# Basic Flags.
Invalid   = 0 #00
Continue  = 1 #01
Matching  = 2 #10
Satisfied = 3 #11

def Any():
    'Matches anything.'
    def init():
        def apply(token):
            return Satisfied
        return (apply, Satisfied)
    return init

def Null():
    'Matches nothing.'
    def init():
        def apply(token):
            return Invalid
        return (apply, Matching)
    return init

def Member(*elements):
    'Matches tokens that are in elements.'
    def init():
        def apply(token):
            return Satisfied if token in elements else Invalid
        return (apply, Satisfied)
    return init

def MemberRange(min, max):
    'Matches tokens where: min <= token <= max.'
    def init():
        def apply(token):
            return Satisfied if min <= token <= max else Invalid
        return (apply, Satisfied)
    return init

def Unique(min=1, max=1):
    'Matches tokens so long as each kind follows a Range constraint.'
    def init():
        tracker = dict()
        range = Range(min, max)
        def apply(token):
            return tracker.getdefault(token, range())(token)
        return (apply, range()(None))
    return init

def Range(min=0, max=None):
    'Matches count tokens where: min <= count <= max.'
    def init():
        self = Bunch(count=-1)
        def apply(token):
            self.count += 1
            if self.count < min:
                return Continue
            if max != None:
                if self.count == max:
                    return Matching
                if self.count > max:
                    return Invalid
            return Satisfied

        return (apply, apply(None))
    return init

def Single():
    'Matches any one token.'
    def init():
        self = Bunch(state=Matching)
        def apply(token):
            (temp, self.state) = (self.state, Invalid)
            return temp
        return (apply, Continue)
    return init

def Parallel(*constraints):
    'Apply all constraints at the same time.'
    def init():
        # Call the init function for all constraints.
        applies = []
        status = Satisfied
        for constraint in constraints:
            apply, substatus = constraint()
            applies.append(apply)
            status &= substatus

        def apply(token):
            status = Satisfied
            for constraint in constraints:
                status &= constraint(token)
            return status

        return (apply, status)
    return init

def Sequence(*constraints):
    'Apply each constraint serially.'
    pass

def Any(*constraints):
    'Apply any and all constraints.'
    pass

def Attribute(name, constraint):
    'Apply constraint to the named token attribute.'
    def init():
        constraint_apply, status = constraint()
        def apply(token):
            return constraint_apply(getattr(token, name))
        return (apply, status)
    return init

# OR...
Single = partial(Range, min=1, max=1)

def match(constraint, tokens):
    apply, status = constraint() 

    for token in tokens:
        if not status & Continue:
            # The last status indicated no continue so this
            # token is outside of the spec.
            status = Invalid
            break

        status = apply(token)

    return status & Matching and True

# Helper class to create mutable state. Javascript has this for free.
class Bunch(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    __call__ = __init__

# Unit Testing
import unittest
from pdb import set_trace as D

class TestBasic(unittest.TestCase):
    def setUp(self):
        pass

    def testNull(self):
        self.assertTrue(match(
            Null(),
            []))

        self.assertFalse(match(
            Null(),
            [1]))
        
    def testMember(self):
        self.assertTrue(
            match(
                Member(*range(10)),
                range(10)))

        self.assertFalse(
            match(
                Member(*range(9)),
                range(10)))

    def testAttribute(self):
        tokens = [Bunch(x=1,y=2,z=3) for i in range(2)]
        result = match(
            Attribute('x',Member(1)),
            tokens)
        self.assertTrue(result)

        result = match(
            Attribute('y',Member(1)),
            tokens)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
