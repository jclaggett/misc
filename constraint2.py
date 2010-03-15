# Verdict Flags.
Invalid   = 0 # 00 # Not matching and don't continue.
Continue  = 1 # 01 # Not matching but continue.
Matching  = 2 # 10 # Matching but don't continue.
Satisfied = 3 # 11 # Matching and continue.

# Helper class to create mutable state.
class Bunch(dict):
    def __init__(self, **kwds):
        self.update(kwds)
        self.__dict__ = self
    __call__ = __init__

# Utility functions that work with constraints.
def match(constraint, tokens):
    'Compare constraint against a list of tokens.'
    apply, verdict = instance(constraint) 

    for token in tokens:
        if not verdict & Continue:
            # The previous verdict indicated no continue so this
            # token stream can never match.
            verdict = Invalid
            break

        verdict = apply(token)

    return bool(verdict & Matching)

def instance(constraint):
    'Create a new instance of the constraint and manage/hide the state.'
    state, verdict = constraint.init()
    wrapped = Bunch(state=state)
    def wrapper(token):
        wrapped.state, verdict = constraint.apply(wrapped.state, token)
        return verdict
    return wrapper, verdict

# Library of constraints.
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
        return apply(state, None)

    def apply(state, token):
        state.count += 1
        verdict = Satisfied
        if state.count < min:
            verdict = Continue
        elif max != None:
            if state.count == max:
                verdict = Matching
            elif state.count > max:
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
    'Matches all constraints.'
    def init():
        state = []
        verdict = Satisfied
        for apply, subverdict in map(instance, constraints):
            state.append(apply)
            verdict &= subverdict
        return state, verdict

    def apply(state, token):
        verdict = Satisfied
        for apply in state:
            verdict &= apply(token)
        return state, verdict

    return Bunch(init=init, apply=apply)

def Or(*constraints):
    'Matches at least one constraint.'
    def init():
        state = []
        verdict = Invalid
        for apply, subverdict in map(instance, constraints):
            state.append(apply)
            verdict |= subverdict
        return state, verdict

    def apply(state, token):
        verdict = Invalid
        for apply in state:
            verdict |= apply(token)
        return state, verdict

    return Bunch(init=init, apply=apply)

def Group(*constraints, **kwds):
    'Matches all constraints in any order limited by pconstraint.'
    pconstraint = kwds.get('constraint', Any())

    def init():
        pstate, pverdict = pconstraint.init()
        return [ (pstate, pverdict, None, None, Matching) ], pverdict

    def apply(paths, token):
        # Calculate the new state (the list of candidate paths).
        new_paths = []
        for pstate, pverdict, id, apply, verdict in paths:

            if verdict & Continue:
                # Apply the token to this path
                new_verdict = apply(token)

                if new_verdict != Invalid:
                    new_paths.append((pstate, pverdict, id, apply, new_verdict))

            if verdict & Matching:
                # Search for new paths
                for new_id, constraint in enumerate(constraints):
                    new_pstate, new_pverdict = pconstraint.apply(pstate, new_id)
                    if new_pverdict != Invalid:
                        new_apply, initial_verdict = instance(constraint)
                        if initial_verdict & Continue:
                            new_verdict = new_apply(token)
                            if new_verdict != Invalid:
                                new_paths.append((new_pstate, new_pverdict,
                                    new_id, new_apply, new_verdict))

        # Calculate the verdict as the logical union of all path verdicts.
        final_verdict = Invalid
        for pstate, pverdict, id, apply, verdict in new_paths:
            final_verdict |= pverdict

        print 'old %d -> new %d' % (len(paths), len(new_paths))
        return new_paths, final_verdict

    return Bunch(init=init, apply=apply)

def Attribute(name, constraint):
    'Apply constraint to the named token attribute.'
    def init():
        return instance(constraint)
    def apply(state, token):
        return state, state(getattr(token, name))
    return Bunch(init=init, apply=apply)

# Unit Testing
import unittest
from pdb import set_trace as D

class TestBasic(unittest.TestCase):
    def setUp(self):
        pass

    def match(self, constraint, tokens):
        return self.assertTrue(
            match(constraint, tokens)
            )

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

    def testMemberRange(self):
        c = MemberRange(1,6)
        self.match(c, [1,2,3,4,5,6,1,2,3,4,5,6])
        self.nomatch(c, [0])
        self.nomatch(c, [7])

    def testRange(self):
        c = Range(min=1,max=3)
        self.nomatch(c, [])
        self.match(c, [1])
        self.match(c, '11')
        self.match(c, '111')
        self.nomatch(c, '1111')

        c = Range(min=2,max=None)
        self.nomatch(c, '')
        self.nomatch(c, '1')
        self.match(c, '11')
        self.match(c, '111')
        self.match(c, '1111')

    def testAnd(self):
        c = And(Null())
        self.match(c, [])
        self.nomatch(c, [1])

        c = And(Any(), Any())
        self.match(c, [])
        self.match(c, [1])
        self.match(c, [1,1])

        c = And(Null(), Any())
        self.match(c, [])
        self.nomatch(c, [1])
        self.nomatch(c, [1,1])

        c = And(Range(1,2), Member('abc'))
        self.match(c, 'a')
        self.match(c, 'bc')
        self.nomatch(c, 'abc')
        self.nomatch(c, '')

    def testOr(self):
        c = Or(Range(1,1), Range(3,4))
        self.nomatch(c, '')
        self.match(c, 'a')
        self.nomatch(c, 'ab')
        self.match(c, 'abc')
        self.match(c, 'abcd')
        self.nomatch(c, 'abcde')

    def testGroup(self):
        digits = MemberRange('0','9')
        dashes = Member('-')

        digit = And(Single(), digits)
        dash = And(Single(), dashes)

        areacode = And(Range(min=3, max=4), digits)
        self.match(areacode, '123')

        phone = Group(areacode, dashes)
        self.match(phone, '123-456-7890')

    def testAttribute(self):
        tokens = [Bunch(x=1,y=2,z=3) for i in range(2)]
        self.match( Attribute('x', Member([1])), tokens)
        self.nomatch( Attribute('y', Member([1])), tokens)

if __name__ == '__main__':
    unittest.main()
