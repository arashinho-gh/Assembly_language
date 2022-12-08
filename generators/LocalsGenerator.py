from tempfile import TemporaryDirectory


class LocalGenerator():
    
    def __init__(self, func_index ,local_var, arguments):
        self.func_index = func_index
        self.local_var = local_var
        self.arguments = arguments
    
    
    def generate(self):
        
        """Creating the Local Variables"""
        print("; Allocating Local Variables")
        for n in reversed(self.local_var):
            print(f'{str(n+":"):<9}\t .EQUATE {self.local_var[n][0]}')
            max = self.local_var[n][0]
        
        """Creating the parameters"""
        print("; Allocating function Parameters")
        temp =0
        for n in self.arguments:
            max += 2
            print(f"{n}:\t\t .EQUATE {max + self.arguments[n]}")
            temp = max + self.arguments[n]
            
        """returning the size of the retVal"""
        return self.arguments,temp+2