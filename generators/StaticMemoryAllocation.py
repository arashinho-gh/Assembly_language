
class StaticMemoryAllocation():

    def __init__(self, global_vars: dict()) -> None:
        self.global_vars = global_vars

    def generate(self):
        print('; Allocating Global (static) memory')

        """creates an alias for each of the global variables"""
        for index, n in enumerate(self.global_vars):
            self.global_vars[n].append(f'Var_{index}')

        """iterates through a dictionary of the global variables"""
        for n in self.global_vars:
            print(f'{str(self.global_vars[n][2]+":"):<9}\t{self.global_vars[n][0]} {self.global_vars[n][1]}') # reserving memory
