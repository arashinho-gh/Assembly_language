import ast
LabeledInstruction = tuple[str, str]

class FuncTranslate(ast.NodeVisitor):
    """We supports assignments and input/print calls"""
    
    def __init__(self, function_index) -> None:
        self.__instructions = list()
        self.__should_save = True
        self.__current_variable = None
        self.__elem_id = 0
        self._initializes = set()
        #function attributes
        self.retVal = False
        self.function = function_index

    def finalize(self):
        return (self.__instructions, self.retVal)

    def visit_Assign(self, node):
        # remembering the name of the target
        self.__current_variable = node.targets[0].id
        # Checking if a return value of function is saved in the variables
        if (type(node.value)) == ast.Call:
            if node.value.func.id not in ['int', 'input', 'print']:
                self.retVal = True
        self.visit(node.value)
        if isinstance(node.value, ast.Constant):
            self.__record_instruction(f'LDWA {node.value.value},i')
            self.__record_instruction(f'STWA {self.__current_variable},s')
            self._initializes.add(node.targets[0].id)
        if self.__should_save and not isinstance(node.value, ast.Constant):
            self.__record_instruction(f'STWA {self.__current_variable},s')
            # Checking if a return value of function is saved in the variables
            if (type(node.value)) == ast.Call:
                if node.value.func.id not in ['int', 'input', 'print']:
                    self.__record_instruction(f'ADDSP 2,s')
        else:
            self.__should_save = True
        self.__current_variable = None
    
    def visit_Name(self, node):
        self.__record_instruction(f'LDWA {node.id},s')

    def visit_BinOp(self, node):
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
                self.__record_instruction(f'DECI {self.__current_variable},s')
                self.__should_save = False # DECI already save the value in memory
            case 'print':
                # We are only supporting integers for now
                self.__record_instruction(f'DECO {node.args[0].id},s')
            case _:
                #In case a function is called
                self.__record_instruction(f'SUBSP {len(node.args)*2},i')
                for index, instruction in enumerate(node.args):
                    self.__record_instruction(f'LDWA {instruction.id},s')
                    self.__record_instruction(f'STWA {index*2},s')
                self.__record_instruction(f'CALL {node.func.id}')
                self.__record_instruction(f'ADDSP {len(node.args)*2},i')

    def visit_While(self, node):
        loop_id = self.__identify()
        inverted = {
            ast.Lt:  'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:  'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT', # '>=' in the code means we branch if '<'
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

    def visit_Return(self, node):
        self.__record_instruction(f'LDWA {node.value.id},s')
        self.__record_instruction(f'STWA retVal{self.function},s')
        self.retVal = True

    def __record_instruction(self, instruction, label = None):
        self.__instructions.append((label, instruction))
    
    def __access_memory(self, node, instruction, label = None):
        if isinstance(node, ast.Constant):
            self.__record_instruction(f'{instruction} {node.value},i', label)
        elif node.id[0] == '_' and node.id[1:].isupper():
            self.__record_instruction(f'{instruction} {node.id},i', label)
        else:
            self.__record_instruction(f'{instruction} {node.id},s', label)
    
    def __identify(self):
        result = self.__elem_id
        self.__elem_id = self.__elem_id + 1
        return result