

class A:
    a = 1

B = A


class A(B):
    b = 1


print(A.b)
print(B.a)