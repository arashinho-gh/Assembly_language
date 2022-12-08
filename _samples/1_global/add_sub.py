value = int(input())
_UNIV = 42
result = value + _UNIV
variable = 3
result = result - variable
result = result - 1
print(result)

## PEP-9 code
## BR program 
## value: .BLOCK 2
## _UNIV: .WORD 42
## result: .BLOCK 2
## variable: .WORD 3
## program: DECI value,d
##          LDWA value,d
##          ADDA _UNIV,d
##          STWA result,d
##          SUBA variable,d
##          STWA result,d
##          SUBA 1,i
##          STWA result,d
##          DECO result,d
##          .END