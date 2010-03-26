# Verdict Flags.
Invalid   = 0b00 # Not matching and don't continue.
Continue  = 0b01 # Not matching but continue.
Matching  = 0b10 # Matching but don't continue.
Satisfied = 0b11 # Matching and continue.

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
    wrapped = dict(state=state)
    def wrapper(token):
        wrapped['state'], verdict = apply(wrapped['state'], token)
        return verdict
    return wrapper, verdict

# Library of constraints.

# Trivial contratints.

def Any():
    'Matches anything.'
    def init():              return None, Satisfied
    def apply(state, token): return state, Satisfied
    return init, apply

def Null():
    'Matches nothing.'
    def init():              return None, Matching
    def apply(state, token): return state, Invalid
    return init, apply

# Token value constraints.

def Member(elements):
    'Matches tokens that are in elements.'
    elements = set(elements) # Redefine elements as a set.
    def init():
        return None, Satisfied
    def apply(state, token):
        return state, Satisfied if token in elements else Invalid
    return init, apply

def Between(min, max):
    'Matches tokens where: min <= count <= max.'
    def init():
        return None, Satisfied

    def apply(state, token):
        return state, Satisfied if min <= token <= max else Invalid

    return init, apply

def Ascending():
    'Matches tokens so long the current is greater than the previous.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return token, Satisfied if state <= token else Invalid
    return init, apply

def Alternate():
    'Matches tokens so long as they occur non-consecutively.'
    def init():
        return None, Satisfied
    def apply(state, token):
        return token, Satisfied if state != token else Invalid
    return init, apply

def Unique():
    'Matches tokens so long as there are no repeats.'
    def init():
        return set(), Satisfied

    def apply(state, token):
        if token in state:
            return state, Invalid
        else:
            state.add(token)
            return state, Satisfied

    return init, apply

def Range(*args):
    'Matches tokens so that their values step from min to max.'
    if   len(args) == 1: min, max, step = 0, args[0], 1
    elif len(args) == 2: min, max, step = args[0], args[1], 1
    elif len(args) == 3: min, max, step = args
    else: raise Error('Too many arguments.')

    def init():
        junk, verdict = apply(min, min)
        return min, verdict

    def apply(state, token):
        if token != state:
            return state, Invalid
        if token < max-step:
            return state+step, Continue
        else:
            return state+step, Satisfied

    return init, apply

def Attribute(name, constraint):
    '''Apply constraint to the tokens' named attribute.'''
    def init():
        return instance(constraint)
    def apply(state, token):
        return state, state(getattr(token, name))
    return init, apply

def Key(key, constraint):
    '''Apply constraint to the tokens' keyed index.'''
    def init():
        return instance(constraint)
    def apply(state, token):
        return state, state(token[key])
    return init, apply

# Token number constraints.

def Single():
    'Matches any one token.'
    def init():
        return Matching, Continue
    def apply(state, token):
        return Invalid, state
    return init, apply

def Repeat(min=0, max=None):
    'Matches the number of tokens where: min <= count <= max.'
    def init():
        return apply(0, None)

    def apply(state, token):
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

    return init, apply

def Enumerate(constraint):
    'Matches the constraint against the number of tokens (not token values).'
    c_init, c_apply = constraint

    def init():
        c_state, c_verdict = c_init()
        return apply((0, c_state), None)

    def apply(state, token):
        count, c_state = state
        c_state, c_verdict = c_apply(c_state, count)
        return (count + 1, c_state), c_verdict

    return init, apply

# Combining constraints.

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

def Sequence(*constraints):
    'Matches a sequence of constraints.'
    return Group(*constraints, meta=Range(len(constraints)))

def Group(*constraints, **kwds):
    'Matches all constraints in any order limited by meta-constraint.'

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
                # Apply the token to this path.
                new_verdict = apply(token)

                if new_verdict != Invalid:
                    new_paths.append((m_state, m_verdict,
                        id, apply, new_verdict))

            if verdict & Matching:
                # Search for new paths.
                for new_id, constraint in enumerate(constraints):
                    new_m_state, new_m_verdict = meta_apply(m_state, new_id)
                    if new_m_verdict != Invalid:
                        new_apply, initial_verdict = instance(constraint)
                        if initial_verdict & Continue:
                            new_verdict = new_apply(token)
                            if new_verdict != Invalid:
                                new_paths.append((new_m_state, new_m_verdict,
                                    new_id, new_apply, new_verdict))

        final_verdict = Invalid
        for m_state, m_verdict, id, apply, verdict in new_paths:
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

    return init, apply

if __name__ == '__main__':
    from constraint_tests import *
    unittest.main()

