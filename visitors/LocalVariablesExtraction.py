import ast

class LocalVariablesExtraction(ast.NodeVisitor):
    """
        We extract all the local variables and the 
    """
    def __init__(self, func_index) -> None:
        super().__init__()
        self.results = {}
        self.arguments = {}
        self.func_index = f"F{func_index}"
    
    """visiting the local variables"""
    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")

        if node.targets[0].id not in self.results and node.targets[0].id not in self.arguments :
            for variable in self.results:
                    self.results[variable][0] += 2
            self.results[node.targets[0].id] = [0, len(self.results)]


    """visiting the parameters"""
    def visit_arguments(self, node):
        for index,argument in enumerate(node.args):
            self.arguments[argument.arg] = (index+1)*2