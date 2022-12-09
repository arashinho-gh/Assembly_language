import ast

class GlobalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the global (top-level) assignments
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.results = {}

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")

        if isinstance(node.targets[0], ast.Subscript):
            return
            
        """It will only record the first apperance of the global variable"""
        if node.targets[0].id not in self.results:
            if isinstance(node.value, ast.Constant):
                if node.targets[0].id[0] == '_' and node.targets[0].id[1:].isupper():
                    self.results[node.targets[0].id] = ['.EQUATE', node.value.value]
                else:
                    self.results[node.targets[0].id] = ['.WORD', node.value.value]
            elif isinstance(node.value, ast.BinOp) and isinstance(node.value.left, ast.List):
                size = str(node.value.right.value * 2)
                self.results[node.targets[0].id] = ['.BLOCK', size]
            elif isinstance(node.value, ast.BinOp) and isinstance(node.value.right, ast.List):
                size = str(node.value.left.value * 2)
                self.results[node.targets[0].id] = ['.BLOCK', size]     
            else:
                self.results [node.targets[0].id] = ['.BLOCK ','2']


    def visit_FunctionDef(self, node):
        """We do not visit function definitions, they are not global by definition"""
        pass