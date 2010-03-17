# Unit Testing
import unittest
from pdb import set_trace as D
from constraint import *

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
        self.nomatch(c, '')
        self.match(c, '1')
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

    def testKey(self):
        tokens = [Bunch(x=1,y=2,z=3) for i in range(2)]
        self.match( Attribute('x', Member([1])), tokens)
        self.nomatch( Attribute('y', Member([1])), tokens)

if __name__ == '__main__':
    unittest.main()
