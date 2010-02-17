class Constraint(object):

    def start(self):
        return (MiniMe(self),) + self.first()

    def first(self,):
        return (False, True)

    def apply(self, token):
        return (False, True)

    def match(self, tokens):
        (instance,s,n) = self.start()
        if n:
            for token in tokens:
                (s,n) = instance.apply(token)
                if not n: break
        return s

class MiniMe(object):
    def __init__(self, parent):
        self.__dict__.update(parent.__dict__)
        self.__class__ = parent.__class__

