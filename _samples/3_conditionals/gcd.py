a = int(input())
b = int(input())

while a != b:
    if a > b:
        a = a - b
    else:
        b = b - a

print(a) 

"""
Pep-9 manual translation:

BR t1
a: .BLOCK 2
b: .BLOCK 2
t1: DECI a,d
    DECI b,d
test: LDWA a,d
      CPWA b,d
      BREQ end_if
      LDWA a,d
      CPWA b,d
      BRLE else_b
if_b: LDWA a,d
      SUBA b,d
      STWA a,d
      BR test
else_b: LDWA b,d
        SUBA a,d
        STWA b,d
        BR test
end_if: DECO a,d
        .END
"""