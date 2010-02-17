from constraint import Constraint

class Null(Constraint):
    def first(self):
        return (False, False)

class Single(Constraint):
    def apply(self, token):
        return (True, False)

class Range(Constraint):

    def __init__(self, min, max):
        self.min = min
        self.max = max

    def apply(self, token):
        if self.min <= token <= self.max:
            return (True, True)
        else:
            return (False, False)

class Member(Constraint):

    def __init__(self, *elements):
        self.elements = elements

    def apply(self, token):
        if token in self.elements:
            return (True, True)
        else:
            return (False, False)

class Unique(Constraint):

    def __init__(self):
        self.tracker = dict()

    def apply(self, token):
        if self.tracker.has_key(token):
            return (False, False)
        else:
            self.tracker[token] = 1
            return (True, True)

class Modulus(Constraint):

    def __init__(self, divisor):
        self.divisor = divisor
        self.dividend = 0

    def apply(self, token):
        self.dividend += 1
        return (boolean(self.dividend % self.divisor), True)

class All(Constraint):

    def __init__(self, *constraints):
        self.constraints = constraints

    def apply(self, token):
        (m,c) = (True,True)
        for constraint in self.constraints:
            (cm,cc) = constraint.apply(token)
            (m,c) = (m and cm, c and cc)

        return (m,c)

class Sequence(Constraint):

    def __init__(self, *constraints):
        self.constraints = constraints
        self.index = 0

    def apply(self, token):
        (m,c) = self.constraints[self.index].apply(token) 
        if not c and m:
            self.index += 1
        return (self.index == len(self.constraints),
            (c or m) and (self.index < len(self.constraints)))

class Attribute(Constraint):

    def __init__(self, name, constraint):
        self.name = name
        self.constraint = constraint

    def apply(self, token):
        return self.constraint.apply(getattr(token, name))

# Unit Testing Code
import unittest
from pdb import set_trace as D

class TestBasic(unittest.TestCase):
    def setUp(self):
        self.tokens = range(10)

    def testMember(self):
        self.assertTrue(Member(*range(10)).match(self.tokens))
        self.assertFalse(Member(*range(9)).match(self.tokens))

    def testSequence(self):
        c = Sequence(All(Single(),Member(':')), All(Single(),Member('-')), All(Single(),Member(')')))
        self.assertTrue(c.match(':-)'))
        self.assertFalse(c.match(':-'))
        self.assertFalse(c.match(';-)'))

if __name__ == '__main__':
    unittest.main()

