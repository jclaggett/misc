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

def Single():
    'Matches any one token.'
    def init():
        return Matching, Continue

    def apply(state, token):
        return Invalid, state

    return init, apply

def Range(min=0, max=None):
    'Matches count tokens where: min <= count <= max.'
    def init():
        return apply(0, None)

    def apply(count, token):
        verdict = Satisfied
        if count < min:
            verdict = Continue
        elif max != None:
            if count == max:
                verdict = Matching
            elif count > max:
                verdict = Invalid
        return count+1, verdict

    return init, apply

def Ascending():
    'Matches tokens so long the current is greater than the previous.'

    def init():
        return None, Satisfied

    def apply(previous, token):
        return token, Satisfied if previous <= token else Invalid

    return init, apply

def Count(*args):
    'Matches each step from min to max.'

    if len(args) == 1:
        min = 0
        max = args[0]
        step = 1
    elif len(args) == 2:
        min = args[0]
        max = args[1]
        step = 1
    elif len(args) == 3:
        min = args[0]
        max = args[1]
        step = args[2]
    else:
        raise Error('Invalid number of arguments.')

    def init():
        if min < max:
            verdict = Continue
        elif min == max:
            verdict = Matching
        elif min > max:
            verdict = Invalid
        return min, verdict

    def apply(state, token):
        verdict = Invalid

        if state == token:
            state += step
            if state < max:
                verdict = Continue
            elif state >= max:
                verdict = Matching

        return state, verdict

    return init, apply

def Unique():
    'Matches tokens so long as there are no repeats.'
    def init():
        state = dict()
        return state, Satisfied

    def apply(state, token):
        verdict = Invalid

        if not state.has_key(token):
            verdict = Satisfied
            state[token] = True

        return state, verdict

    return init, apply

def Alternate():
    'Matches tokens so long as they occur non-consecutively.'
    def init():
        return None, Satisfied

    def apply(state, token):
        return token, Satisfied if state.prev != token else Invalid

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

def Sequence(*constraints):
    'Matches a sequence of constraints.'
    return Group(*constraints, meta=Count(len(constraints)))

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

