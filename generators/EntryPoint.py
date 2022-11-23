from dis import Instruction


class EntryPoint():

    def __init__(self, instructions, global_vars) -> None:
        self.__instructions = instructions
        self.__global_vars = global_vars

    def generate(self):
        print('; Top Level instructions')

        """Replaces the global variables in the top level instructions"""
        def translate(instr):
            if len(instr.split()) > 1 and len(instr.split(',')) > 1:
                instruction = instr.split(',')[0].split()[1]
                if instruction in self.__global_vars.keys():
                    instruction = self.__global_vars[instruction][2]
                command = instr.split()[0]
                address_mode = instr[-2:]
                instr = f'{command} {instruction}{address_mode}'
            return instr

        """Prints all the instructions"""
        for label, instr in self.__instructions:
            instr = translate(instr)
            s = f'\t\t{instr}' if label == None else f'{str(label+":"):<9}\t{instr}'
            print(s)
        

