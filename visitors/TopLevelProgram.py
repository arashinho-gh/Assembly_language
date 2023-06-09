import ast
LabeledInstruction = tuple[str, str]

class TopLevelProgram(ast.NodeVisitor):
    """We supports assignments and input/print calls"""
    
    def __init__(self, entry_point) -> None:
        super().__init__()
        self.__instructions = list()
        self.__record_instruction('NOP1', label=entry_point)
        self.__should_save = True
        self.__current_variable = None
        self.__elem_id = 0
        self._initializes = set()
        self.retVal = False

    def finalize(self):
        self.__instructions.append((None, '.END'))
        return self.__instructions

    ####
    ## Handling Assignments (variable = ...)
    ####

    def visit_Assign(self, node):
        # remembering the name of the target
        if isinstance(node.targets[0], ast.Subscript):
            self.__current_variable = node.targets[0].value.id
        else:
            self.__current_variable = node.targets[0].id
        # Checking if a return value of function is saved in the variables
        if (type(node.value)) == ast.Call:
            if node.value.func.id not in ['int', 'input', 'print']:
                self.retVal = True
        self.visit(node.value)
        if isinstance(node.value, ast.Constant):
            if self.__current_variable in self._initializes or isinstance(node.targets[0], ast.Subscript):
                if isinstance(node.targets[0], ast.Subscript):
                    self.__record_instruction(f'LDWA {node.value.value},i')
                    self.__access_memory(node.targets[0].slice, "LDWX")
                    self.__record_instruction(f'ASLX')
                    self.__record_instruction(f'STWA {self.__current_variable},x')
                else:
                    self.__record_instruction(f'LDWA {node.value.value},i')
                    self.__record_instruction(f'STWA {self.__current_variable},d')
            if isinstance(node.targets[0], ast.Subscript):
                self._initializes.add(node.targets[0].value.id)
            else:
                self._initializes.add(node.targets[0].id)
        elif isinstance(node.targets[0], ast.Subscript):
                self.__access_memory(node.targets[0].slice, "LDWX")
                self.__record_instruction(f'ASLX')
                self.__record_instruction(f'STWA {self.__current_variable},x')
        
        if self.__should_save and not isinstance(node.targets[0], ast.Subscript) and not isinstance(node.value, ast.Constant) and not (isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Mult)):
            self.__record_instruction(f'STWA {self.__current_variable},d')
            # Checking if a return value of function is saved in the variables
            if (type(node.value)) == ast.Call:
                if node.value.func.id not in ['int', 'input', 'print']:
                    self.__record_instruction(f'ADDSP 2,i')
        else:
            self.__should_save = True
        self.__current_variable = None
    
    def visit_Name(self, node):
        self.__record_instruction(f'LDWA {node.id},d')

    def visit_BinOp(self, node):
        if isinstance(node.left, ast.Subscript) or isinstance(node.right, ast.Subscript):
            self.__record_instruction(f'LDWA 0,i')
            # left-argument
            if not isinstance(node.left, ast.Subscript):
                self.__access_memory(node.left, 'ADDA')
            else:
                self.__access_memory(node.left.slice, 'LDWX')
                self.__record_instruction(f'ASLX')
                self.__record_instruction(f'ADDA {node.left.value.id},x')

            # right-argument
            if isinstance(node.right, ast.Subscript):
                self.__access_memory(node.right.slice, 'LDWX')
                self.__record_instruction(f'ASLX')

            # operation
            if isinstance(node.op, ast.Add):
                if isinstance(node.right, ast.Subscript):
                    self.__record_instruction(f'ADDA {node.right.value.id},x')
                else:
                    self.__access_memory(node.right, 'ADDA')
            else:
                if isinstance(node.right, ast.Subscript):
                    self.__record_instruction(f'SUBA {node.right.value.id},x')
                else:
                    self.__access_memory(node.right, 'SUBA') 
            return

        if isinstance(node.op, ast.Mult):
            return
        self.__access_memory(node.left, 'LDWA')
        if isinstance(node.op, ast.Add):
            self.__access_memory(node.right, 'ADDA')
        elif isinstance(node.op, ast.Sub):
            self.__access_memory(node.right, 'SUBA')
        else:
            raise ValueError(f'Unsupported binary operator: {node.op}')

    def visit_Call(self, node):
        match node.func.id:
            case 'int': 
                # Let's visit whatever is casted into an int
                self.visit(node.args[0])
            case 'input':
                # We are only supporting integers for now
                self.__record_instruction(f'DECI {self.__current_variable},d')
                self.__should_save = False # DECI already save the value in memory
            case 'print':
                # We are only supporting integers for now
                if isinstance(node.args[0], ast.Subscript):
                    self.__access_memory(node.args[0].slice, 'LDWX')
                    self.__record_instruction(f'ASLX')
                    self.__record_instruction(f'DECO {node.args[0].value.id},x')
                else:
                    self.__record_instruction(f'DECO {node.args[0].id},d')
            case _:
                #raise ValueError(f'Unsupported function call: { node.func.id}')
                if (self.retVal):
                    self.__record_instruction(f'SUBSP {(len(node.args)*2) + 2},i')
                else:
                    self.__record_instruction(f'SUBSP {len(node.args)*2},i')
                for index, instruction in enumerate(node.args):
                    self.__record_instruction(f'LDWA {instruction.id},d')
                    self.__record_instruction(f'STWA {index*2},s')
                self.__record_instruction(f'CALL {node.func.id}')
                self.__record_instruction(f'ADDSP {len(node.args)*2},i')
                if (self.retVal):
                    self.__record_instruction(f'LDWA 0,s')


    ####
    ## Handling While loops (only variable OP variable)
    ####

    def visit_While(self, node):
        for n in node.body:
            if type(n) == ast.Assign:
                if isinstance(n.targets[0], ast.Subscript):
                    self._initializes.add(n.targets[0].value.id)
                else:
                    self._initializes.add(n.targets[0].id)
        loop_id = self.__identify()
        inverted = {
            ast.Lt:  'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:  'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT', # '>=' in the code means we branch if '<'
            ast.Eq: 'BRNE', # '!=' in the code means we branch if '='
            ast.NotEq: 'BREQ', # '=' in the code means we branch if '!='
        }
        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label = f'test_{loop_id}')
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        # Branching is condition is not true (thus, inverted)
        self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_l_{loop_id}')
        # Visiting the body of the loop
        for contents in node.body:
            self.visit(contents)
        self.__record_instruction(f'BR test_{loop_id}')
        # Sentinel marker for the end of the loop
        self.__record_instruction(f'NOP1', label = f'end_l_{loop_id}')

    ####
    ## Handling Conditionals (if, elif, else) 
    ####

    def visit_If(self, node):
        loop_id = self.__identify()
        inverted = {
            ast.Lt:  'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:  'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT', # '>=' in the code means we branch if '<'
            ast.Eq: 'BRNE', # '!=' in the code means we branch if '='
            ast.NotEq: 'BREQ', # '=' in the code means we branch if '!='
        }
        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label = f'test_{loop_id}')
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        # Branching is condition is not true (thus, inverted)
        self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_if_{loop_id}')
        # Visiting the body of the loop
        for contents in node.body:
            self.visit(contents)
        self.__record_instruction(f'BR exit_{loop_id}')
        # marker for else
        self.__record_instruction(f'NOP1', label = f'end_if_{loop_id}')
        if len(node.orelse) != 0:
            for item in node.orelse:
                self.visit(item)
        # marker for if exit
        self.__record_instruction(f'NOP1', label = f'exit_{loop_id}')


    ####
    ## Not handling function calls 
    ####

    def visit_FunctionDef(self, node):
         """We do not visit function definitions, they are not top level"""
         pass

    ####
    ## Helper functions to 
    ####

    def __record_instruction(self, instruction, label = None):
        self.__instructions.append((label, instruction))

    def __access_memory(self, node, instruction, label = None):
        if isinstance(node, ast.Constant):
            self.__record_instruction(f'{instruction} {node.value},i', label)
        elif node.id[0] == '_' and node.id[1:].isupper():
            self.__record_instruction(f'{instruction} {node.id},i', label)
        else:
            self.__record_instruction(f'{instruction} {node.id},d', label)

    def __identify(self):
        result = self.__elem_id
        self.__elem_id = self.__elem_id + 1
        return result