from functools import partial

# Verdict Flags.
Invalid   = 0 # 00 # Not matching and don't continue.
Continue  = 1 # 01 # Not matching but continue.
Matching  = 2 # 10 # Matching and don't continue.
Satisfied = 3 # 11 # Matching and continue.

def Null():
    'Matches nothing.'
    def init():
        return None, Matching
    def apply(state, token):
        return state, Invalid
    return Bunch(init=init, apply=apply)

def Any():
    'Matches anything.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return state, Satisfied
    return Bunch(init=init, apply=apply)

def Member(elements):
    'Matches tokens that are in elements.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return state, Satisfied if token in elements else Invalid
    return Bunch(init=init, apply=apply)

def MemberRange(min, max):
    'Matches tokens where: min <= token <= max.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return state, Satisfied if min <= token <= max else Invalid
    return Bunch(init=init, apply=apply)

def Range(min=0, max=None):
    'Matches count tokens where: min <= count <= max.'
    def init():
        state = Bunch(count=-1)
        verdict = apply(None)
        return state, verdict

    def apply(state, token):
        state.count += 1
        verdict = Satisfied
        if state.count < min:
            verdict = Continue
        elif max != None:
            if self.count == max:
                verdict = Matching
            elif self.count > max:
                verdict = Invalid
        return state, verdict

    return Bunch(init=init, apply=apply)

def Unique(min=1, max=1):
    'Matches tokens so long as each kind follows a Range constraint.'
    def init():
        range = Range(min, max)
        starting_state, verdict = range.init()
        state = Bunch(
            tokens=dict(),
            starting_state=starting_state,
            apply=range.apply)
        return state, verdict

    def apply(state, token):
        state.tokens[token], verdict = state.apply(
            state.tokens.get(token, state.starting_state), token)
        return state, verdict

    return Bunch(init=init, apply=apply)

def Single():
    'Matches any one token.'
    def init():
        return Bunch(toggle=Matching), Continue

    def apply(state, token):
        verdict, state.toggle = state.toggle, Invalid
        return state, verdict

    return Bunch(init=init, apply=apply)

def And(*constraints):
    'Apply all constraints at the same time.'
    def init():
        state = []
        final_verdict = Satisfied
        for constraint in constraints:
            # Wrap constraints so their states are handled cleanly.
            apply, verdict = wrap(constraint)
            state.append(apply)
            final_verdict &= verdict
        return state, final_verdict

    def apply(state, token):
        verdict = Satisfied
        for apply in state:
            verdict &= apply(token)
        return state, verdict

    return Bunch(init=init, apply=apply)

def Sequence(*constraints):
    'Apply each constraint serially.'
    pass

def Parallel(*constraints):
    'Apply any and all constraints.'
    pass

def Attribute(name, constraint):
    'Apply constraint to the named token attribute.'
    def init():
        return wrap(constraint)
    def apply(state, token):
        return state, state(getattr(token, name))
    return Bunch(init=init, apply=apply)

def match(constraint, tokens):
    apply, verdict = wrap(constraint) 

    for token in tokens:
        if not verdict & Continue:
            # The previous verdict indicated no continue so this
            # token stream can never match.
            verdict = Invalid
            break

        verdict = apply(token)

    return bool(verdict & Matching)

def wrap(constraint):
    state, verdict = constraint.init()
    wrapped = Bunch(state=state)
    def wrapper(token):
        wrapped.state, verdict = constraint.apply(wrapped.state, token)
        return verdict
    return wrapper, verdict

# Helper class to create mutable state.
class Bunch(dict):
    def __init__(self, **kwds):
        self.update(kwds)
        self.__dict__ = self
    __call__ = __init__

# Unit Testing
import unittest
from pdb import set_trace as D

class TestBasic(unittest.TestCase):
    def setUp(self):
        pass

    def match(self, constraint, tokens):
        return self.assertTrue(match(constraint, tokens))

    def nomatch(self, constraint, tokens):
        return self.assertFalse(match(constraint, tokens))

    def testNull(self):
        self.match( Null(), [] )
        self.nomatch( Null(), [1] )

    def testAny(self):
        self.match( Any(), [] )
        self.match( Any(), [1, 2, 3] )
        self.match( Any(), [1, 2, 3] * 3 )
        self.match( Any(), range(100) )
        self.match( Any(), 'abcdef' )

    def testMember(self):
        nine, ten = range(9), range(10)
        self.match(Member(ten), nine)
        self.nomatch(Member(nine), ten)

    def testAttribute(self):
        tokens = [Bunch(x=1,y=2,z=3) for i in range(2)]
        self.match( Attribute('x', Member([1])), tokens)
        self.nomatch( Attribute('y', Member([1])), tokens)

if __name__ == '__main__':
    unittest.main()
