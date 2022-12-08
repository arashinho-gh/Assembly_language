
class FuncGenerator():
    def __init__(self, instructions,index, retVal, global_vars, stacks, localVars, args,func_name) -> None:
        self.__instructions = instructions
        self.__index = index
        self.__retVal = retVal
        self.__global_vars = global_vars
        self.stacks = stacks
        self.localVars = localVars #The local variables
        self.func_name = func_name
        self.args = args

    def generate(self):
        
        """Replaces the global variables in the top level instructions"""
        def translate(instr):
            if len(instr.split()) > 1 and len(instr.split(',')) > 1:
                instruction = instr.split(',')[0].split()[1]
                if instruction in self.__global_vars.keys() and instruction not in self.args.keys() and instruction not in self.localVars.keys():
                    instruction = self.__global_vars[instruction][2]
                command = instr.split()[0]
                address_mode = instr[-2:]
                instr = f'{command} {instruction}{address_mode}'
            return instr

        """Creates the return variable"""
        if self.__retVal:
            print(";Assigning return variables")
            print(f'retVal{self.__index}:\t.EQUATE {self.stacks}')

        """Creates the stack at the beginning of the functions"""
        if len(self.localVars) != 0:
            print(";Assigning function definitions")
            print(f'{self.func_name}:\t\tSUBSP {len(self.localVars) * 2},i')
        else:
            print(f'{self.func_name}:', end='')

        """Prints all the instructions"""
        for label, instr in self.__instructions:
            instr = translate(instr)
            s = f'\t\t{instr}' if label == None else f'{str(label+":"):<9}\t{instr}'
            print(s)
        """Deletes the stack at the end of the function"""
        if not self.__retVal:
            if len(self.localVars) != 0:
                print(f'\t\tADDSP {len(self.localVars) * 2},i')
                print('\t\tRET')