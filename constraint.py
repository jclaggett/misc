# Debugging.
from pdb import set_trace as D

# Verdict Sets.
Invalid = frozenset()
Continue = frozenset([1])
Matching = frozenset([2])
Satisfied = Continue | Matching

# Utility functions that work with constraints.
def match(constraint, tokens):
    'Compare constraint against a list of tokens.'
    init, test = constraint
    state, verdict = init()

    for token in tokens:
        if not verdict >= Continue:
            # The previous verdict indicated no continue so this
            # token stream can never match.
            verdict = Invalid
            break

        state, verdict = test(state, token)

    return verdict >= Matching

# Library of constraints.

# Trivial contratints.

def Any():
    'Matches anything.'
    def init():             return None, Satisfied
    def test(state, token): return state, Satisfied
    return init, test

def Null():
    'Matches nothing.'
    def init():             return None, Matching
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
        return (token, Satisfied) if state <= token else (state, Invalid)
    return init, test

def Alternate():
    'Matches tokens so long as they occur non-consecutively.'
    def init():
        return None, Satisfied
    def test(state, token):
        return (token, Satisfied) if state != token else (state, Invalid)
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
    c_init, c_test = constraint
    def test(state, token):
        return c_test(state, getattr(token, name))
    return c_init, test

def Key(key, constraint):
    '''Apply constraint to the tokens' keyed index.'''
    c_init, c_test = constraint
    def test(state, token):
        return c_test(state, token[key])
    return c_init, test

# Token number constraints.

def Single():
    'Matches any one token.'
    def init():
        return True, Continue
    def test(state, token):
        return (False, Matching) if state else (state, Invalid)
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
            return state, Invalid

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
        if c_verdict == Invalid:
            return state, Invalid
        else:
            return (count + 1, c_state), c_verdict

    return init, test

# Combining constraints.

def And(*constraints):
    'Matches all constraints.'
    def init():
        state = []
        verdict = Satisfied
        for c_init, c_test in constraints:
            c_state, c_verdict = c_init()
            state.append((c_state, c_test))
            verdict &= c_verdict
        return state, verdict

    def test(state, token):
        verdict = Satisfied
        new_state = []
        for c_state, c_test in state:
            c_state, c_verdict = c_test(c_state, token)
            new_state.append((c_state, c_test))
            verdict &= c_verdict
        if verdict == Invalid:
            return state, Invalid
        else:
            return new_state, verdict

    return init, test

def Or(*constraints):
    'Matches at least one constraint.'
    def init():
        state = []
        verdict = Invalid
        for c_init, c_test in constraints:
            c_state, c_verdict = c_init()
            state.append((c_state, c_test))
            verdict |= c_verdict
        return state, verdict

    def test(state, token):
        verdict = Invalid
        new_state = []
        for c_state, c_test in state:
            c_state, c_verdict = c_test(c_state, token)
            new_state.append((c_state, c_test))
            verdict |= c_verdict
        if verdict == Invalid:
            return state, Invalid
        else:
            return new_state, verdict

    return init, test

def Sequence(*constraints):
    'Matches a sequence of constraints.'
    return Group(*constraints, meta=Range(len(constraints)))

def Group(*constraints, **kwds):
    'Matches all constraints in any order limited by meta-constraint.'

    # Get the meta-constraint defaulting to Any().
    m_init, m_test = kwds.get('meta', Any())

    def init():
        m_state, m_verdict = m_init()
        return [ (m_state, m_verdict, None, Matching, None, None) ], m_verdict

    def test(state, token):
        # Calculate the new state (the list of candidate paths).
        new_state = []
        for m_state, m_verdict, c_state, c_verdict, c_test, c_id in state:

            if c_verdict >= Continue:
                # Apply the token to this path.
                new_c_state, new_c_verdict = c_test(c_state, token)

                if new_c_verdict != Invalid:
                    new_state.append((m_state, m_verdict,
                        new_c_state, new_c_verdict, c_test, c_id))

            if c_verdict >= Matching:
                # Search for new paths.
                for new_c_id, (new_c_init,new_c_test) in enumerate(constraints):

                    # Optimization: If the current constraint has no state, it
                    # will match as many tokens as possible so we don't need to
                    # add a new path with this constraint. This needs to be
                    # generalized in the future. Maybe a modified verdict?
                    if new_c_id == c_id and c_state == None: continue

                    new_m_state, new_m_verdict = m_test(m_state, new_c_id)
                    if new_m_verdict == Invalid: continue

                    new_c_state, new_c_verdict = new_c_init()
                    if not new_c_verdict >= Continue: continue

                    new_c_state, new_c_verdict = new_c_test(new_c_state, token)
                    if new_c_verdict == Invalid: continue

                    new_state.append((new_m_state, new_m_verdict,
                        new_c_state, new_c_verdict, new_c_test, new_c_id))

        final_verdict = Invalid
        for m_state, m_verdict, c_state, c_verdict, c_test, c_id in new_state:
            # First, this path will continue if either the current constraint
            # or the meta constraint continues.
            path_continue = Continue & (c_verdict | m_verdict)

            # Second, this path is matching if both the current constraint and
            # the meta constraint are matching.
            path_matching = Matching & (c_verdict & m_verdict)

            # Third, the final verdict is the logical union of each path
            # verdict.
            final_verdict |= path_continue | path_matching

        if final_verdict == Invalid:
            return state, Invalid # Be sure to return the original state if Invalid.
        else:
            return new_state, final_verdict

    return init, test

if __name__ == '__main__':
    from constraint_tests import *
    unittest.main()

