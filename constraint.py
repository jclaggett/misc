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
    init, apply = constraint
    state, verdict = init()
    wrapped = Bunch(state=state)
    def wrapper(token):
        wrapped.state, verdict = apply(wrapped.state, token)
        return verdict
    return wrapper, verdict

# Library of constraints.
def Null():
    'Matches nothing.'
    def init():
        return None, Matching
    def apply(state, token):
        return state, Invalid
    return init, apply

def Any():
    'Matches anything.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return state, Satisfied
    return init, apply

def Member(elements):
    'Matches tokens that are in elements.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return state, Satisfied if token in elements else Invalid
    return init, apply

def MemberRange(min, max):
    'Matches tokens where: min <= token <= max.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return state, Satisfied if min <= token <= max else Invalid
    return init, apply

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

    return init, apply

def Unique(min=1, max=1):
    'Matches tokens so long as each kind follows a Range constraint.'
    def init():
        range_init, range_apply = Range(min, max)
        starting_state, verdict = range_init()
        state = Bunch(
            tokens=dict(),
            starting_state=starting_state,
            apply=range_apply)
        return state, verdict

    def apply(state, token):
        state.tokens[token], verdict = state.apply(
            state.tokens.get(token, state.starting_state), token)
        return state, verdict

    return init, apply

def Alternate():
    'Matches tokens so long as they occur non-consecutively.'
    def init():
        return Bunch(prev=None), Satisfied
    def apply(state, token):
        verdict = Satisfied if state.prev != token else Invalid
        state.prev = token
        return state, verdict

def Single():
    'Matches any one token.'
    def init():
        return Bunch(toggle=Matching), Continue

    def apply(state, token):
        verdict, state.toggle = state.toggle, Invalid
        return state, verdict

    return init, apply

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

    return init, apply

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

    return init, apply

def Group(*constraints, **kwds):
    'Matches all constraints in any order limited by meta-constraint.'

    # Associate an id with each constraint.
    constraints = enumerate(constraints)

    # If the constraints are not ordered, use an explicit list instead of
    # a generator (lazy seq).
    if not kwds.get('ordered', False):
        constraints = list(constraints)

    # Get the meta-constraint defaulting to Any().
    meta_init, meta_apply = kwds.get('meta', Any())

    def init():
        m_state, m_verdict = meta_init()
        return [ (m_state, m_verdict, None, None, Matching) ], m_verdict

    def apply(paths, token):
        # Calculate the new state (the list of candidate paths).
        new_paths = []
        for m_state, m_verdict, id, apply, verdict in paths:

            if verdict & Continue:
                # Apply the token to this path
                new_verdict = apply(token)

                if new_verdict != Invalid:
                    new_paths.append((m_state, m_verdict,
                        id, apply, new_verdict))

            if verdict & Matching:
                # Search for new paths
                for new_id, constraint in constraints:
                    new_m_state, new_m_verdict = meta_apply(m_state, new_id)
                    if new_m_verdict != Invalid:
                        new_apply, initial_verdict = instance(constraint)
                        if initial_verdict & Continue:
                            new_verdict = new_apply(token)
                            if new_verdict != Invalid:
                                new_paths.append((new_m_state, new_m_verdict,
                                    new_id, new_apply, new_verdict))

        # Calculate the verdict as the logical union of all path verdicts.
        final_verdict = Invalid
        for m_state, m_verdict, id, apply, verdict in new_paths:
            final_verdict |= m_verdict

        # print 'old %d -> new %d' % (len(paths), len(new_paths))
        return new_paths, final_verdict

    return init, apply

def Attribute(name, constraint):
    'Apply constraint to the named token attribute.'
    def init():
        return instance(constraint)
    def apply(state, token):
        return state, state(getattr(token, name))
    return init, apply

def Key(key, constraint):
    'Apply constraint to the key in attribute.'
    def init():
        return instance(constraint)
    def apply(state, token):
        return state, state(token[key])
    return init, apply

if __name__ == '__main__':
    from constraint_tests import *
    unittest.main()

