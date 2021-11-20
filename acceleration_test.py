import time
import numpy as np


class A:
    def __init__(self, first):
        self.first = first



    def yes_printed(self):

        print(self.first)
        self.first += 1


class B(A):
    def __init__(self):
        super().__init__(2)


    def printed(self):
        print(self.first)


class C(A):
    def __init__(self):
        super().__init__(2)


    def printed(self):
        print(self.first)


b = B()
c = C()

b.printed()
c.printed()
print('\n')
b.yes_printed()
# c.yes_printed()
print('\n')
b.printed()
c.printed()