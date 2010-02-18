from constraint import constraint

# Basic terms.
Matching = Continue = True
Invalid = (not Matching, not Continue)
Incomplete = (not Matching, Continue)
Complete = (Matching, not Continue)
Satisfied = (Matching, Continue)

@constraint
def Any(self):
    'Matches anything.'
    def apply(token):
        return Satisfied
    return (apply, Satisfied)

@constraint
def Null(self):
    'Matches nothing.'
    def apply(token):
        return Invalid
    return (apply, Complete)

@constraint
def Member(self, *elements):
    'Matches tokens that are in elements.'
    def apply(token):
        return Satisfied if token in elements else Invalid
    return (apply, Satisfied)

@constraint
def MemberRange(self, min, max):
    'Matches tokens where: min <= token <= max.'
    def apply(token):
        return Satisfied if min <= token <= max else Invalid
    return (apply, Satisfied)

@constraint
def Range(self, min=0, max=None):
    'Matches count tokens where: min <= count <= max.'
    self(count=-1)
    def apply(token):
        self.count += 1
        if self.count < min:
            return Incomplete
        if max != None
            if self.count == max:
                return Complete
            if self.count > max:
                return Invalid
        return Satisfied

    return (apply, apply(None))

@constraint
def Single(self):
    'Matches any one token.'
    self(state=Complete)
    def apply(token):
        (temp, self.state) = (self.state, Invalid)
        return temp
    return (apply, Incomplete)
