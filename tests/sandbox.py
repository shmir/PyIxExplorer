from abc import ABC

def m1(name, bases, atts):
    print("m1 called for " + name)
    return type(name, bases, atts)


class C1(ABC, metaclass=m1):
    def __init__(self):
        super().__init__()
        print('inside C1 init')


class C2(C1, metaclass=m1):
    def __init__(self):
        super().__init__()
        print('inside C2 init')


if __name__ == '__main__':
    c = C2()
    print(issubclass(type(c), C1))
