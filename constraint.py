# Verdict Flags.
Invalid   = 0b00 # Not matching and don't continue.
Continue  = 0b01 # Not matching but continue.
Matching  = 0b10 # Matching but don't continue.
Satisfied = 0b11 # Matching and continue.

# Utility functions that work with constraints.
def match(constraint, tokens):
    'Compare constraint against a list of tokens.'
    test, verdict = instance(constraint) 

    for token in tokens:
        if not verdict & Continue:
            # The previous verdict indicated no continue so this
            # token stream can never match.
            verdict = Invalid
            break

        verdict = test(token)

    return bool(verdict & Matching)

# XXX This is not a pure function so try not to use it.
def instance(constraint):
    'Create a new instance of the constraint and manage/hide the state.'
    init, test = constraint
    state, verdict = init()
    wrapped = dict(state=state)
    def wrapper(token):
        wrapped['state'], verdict = test(wrapped['state'], token)
        return verdict
    return wrapper, verdict

# Library of constraints.

# Trivial contratints.

def Any():
    'Matches anything.'
    def init():              return None, Satisfied
    def test(state, token): return state, Satisfied
    return init, test

def Null():
    'Matches nothing.'
    def init():              return None, Matching
    def test(state, token): return state, Invalid
    return init, test

# Token value constraints.

def Member(elements):
    'Matches tokens that are in elements.'
    elements = set(elements) # Redefine elements as a set.
    def init():
        return None, Satisfied
    def test(state, token):
        return state, Satisfied if token in elements else Invalid
    return init, test

def Between(min, max):
    'Matches tokens where: min <= count <= max.'
    def init():
        return None, Satisfied

    def test(state, token):
        return state, Satisfied if min <= token <= max else Invalid

    return init, test

def Ascending():
    'Matches tokens so long the current is greater than the previous.'
    def init():
        return None, Satisfied
    def test(state, token):
        return token, Satisfied if state <= token else Invalid
    return init, test

def Alternate():
    'Matches tokens so long as they occur non-consecutively.'
    def init():
        return None, Satisfied
    def test(state, token):
        return token, Satisfied if state != token else Invalid
    return init, test

def Unique():
    'Matches tokens so long as there are no repeats.'
    def init():
        return set(), Satisfied

    def test(state, token):
        if token in state:
            return state, Invalid
        else:
            state.add(token)
            return state, Satisfied

    return init, test

def Range(*args):
    'Matches tokens so that their values step from min to max.'
    if   len(args) == 1: min, max, step = 0, args[0], 1
    elif len(args) == 2: min, max, step = args[0], args[1], 1
    elif len(args) == 3: min, max, step = args
    else: raise Error('Too many arguments.')

    def init():
        junk, verdict = test(min, min)
        return min, verdict

    def test(state, token):
        if token != state:
            return state, Invalid
        if token < max-step:
            return state+step, Continue
        else:
            return state+step, Satisfied

    return init, test

def Attribute(name, constraint):
    '''Apply constraint to the tokens' named attribute.'''
    def init():
        return instance(constraint)
    def test(state, token):
        return state, state(getattr(token, name))
    return init, test

def Key(key, constraint):
    '''Apply constraint to the tokens' keyed index.'''
    def init():
        return instance(constraint)
    def test(state, token):
        return state, state(token[key])
    return init, test

# Token number constraints.

def Single():
    'Matches any one token.'
    def init():
        return Matching, Continue
    def test(state, token):
        return Invalid, state
    return init, test

def Repeat(min=0, max=None):
    'Matches the number of tokens where: min <= count <= max.'
    def init():
        return test(0, None)

    def test(state, token):
        if state < min:
            return state+1, Continue
        if max == None:
            return state+1, Satisfied
        if state < max:
            return state+1, Satisfied
        if state == max:
            return state+1, Matching
        if state > max:
            return state+1, Invalid

    return init, test

def Enumerate(constraint):
    'Matches the constraint against the number of tokens (not token values).'
    c_init, c_test = constraint

    def init():
        c_state, c_verdict = c_init()
        return test((0, c_state), None)

    def test(state, token):
        count, c_state = state
        c_state, c_verdict = c_test(c_state, count)
        return (count + 1, c_state), c_verdict

    return init, test

# Combining constraints.

def And(*constraints):
    'Matches all constraints.'
    def init():
        state = []
        verdict = Satisfied
        for test, subverdict in map(instance, constraints):
            state.append(test)
            verdict &= subverdict
        return state, verdict

    def test(state, token):
        verdict = Satisfied
        for test in state:
            verdict &= test(token)
        return state, verdict

    return init, test

def Or(*constraints):
    'Matches at least one constraint.'
    def init():
        state = []
        verdict = Invalid
        for test, subverdict in map(instance, constraints):
            state.append(test)
            verdict |= subverdict
        return state, verdict

    def test(state, token):
        verdict = Invalid
        for test in state:
            verdict |= test(token)
        return state, verdict

    return init, test

def Sequence(*constraints):
    'Matches a sequence of constraints.'
    return Group(*constraints, meta=Range(len(constraints)))

def Group(*constraints, **kwds):
    'Matches all constraints in any order limited by meta-constraint.'

    # Get the meta-constraint defaulting to Any().
    meta_init, meta_test = kwds.get('meta', Any())

    def init():
        m_state, m_verdict = meta_init()
        return [ (m_state, m_verdict, None, None, Matching) ], m_verdict

    def test(paths, token):
        # Calculate the new state (the list of candidate paths).
        new_paths = []
        for m_state, m_verdict, id, test, verdict in paths:

            if verdict & Continue:
                # Apply the token to this path.
                new_verdict = test(token)

                if new_verdict != Invalid:
                    new_paths.append((m_state, m_verdict,
                        id, test, new_verdict))

            if verdict & Matching:
                # Search for new paths.
                for new_id, constraint in enumerate(constraints):
                    new_m_state, new_m_verdict = meta_test(m_state, new_id)
                    if new_m_verdict != Invalid:
                        new_test, initial_verdict = instance(constraint)
                        if initial_verdict & Continue:
                            new_verdict = new_test(token)
                            if new_verdict != Invalid:
                                new_paths.append((new_m_state, new_m_verdict,
                                    new_id, new_test, new_verdict))

        final_verdict = Invalid
        for m_state, m_verdict, id, test, verdict in new_paths:
            # First, this path will continue if either the current constraint
            # or the meta constraint continues.
            path_continue = (verdict & Continue) | (m_verdict & Continue)

            # Second, this path is matching if both the current constraint and
            # the meta constraint are matching.
            path_matching = (verdict & Matching) & (m_verdict & Matching)

            # Third, the final verdict is the logical union of each path
            # verdict.
            final_verdict |= path_continue | path_matching

        return new_paths, final_verdict

    return init, test

if __name__ == '__main__':
    from constraint_tests import *
    unittest.main()

